import json
import io
import requests_mock
from freezegun import freeze_time
import demistomock as demisto


DEMISTO_PARAMS = {
    'method': 'GET',
    'url': 'https://your.domain/rest/api/3/auditing/record',
    'max_fetch': 100,
    'first_fetch': '3 days',
    'credentials': {
        'identifier': 'admin@your.domain',
        'password': '123456',
    }
}
URL = 'https://your.domain/rest/api/3/auditing/record'
FIRST_REQUESTS_PARAMS = 'from=2022-04-11T00:00:00.000000&limit=1000&offset=0'
SECOND_REQUESTS_PARAMS = 'from=2022-04-11T00:00:00.000000&limit=1000&offset=1000'


def util_load_json(path):
    with io.open(path, mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


def calculate_next_run(time):
    next_time = time.removesuffix('+0000')
    next_time_with_delta = next_time[:-1] + str(int(next_time[-1]) + 1)
    return next_time_with_delta


@freeze_time('2022-04-14T00:00:00Z')
def test_fetch_incidents_few_incidents(mocker):
    """
    Given
        - raw response of the http request
    When
        - fetching incidents
    Then
        - check the number of incidents that are being created
        check that the time in last_run is the on of the latest incident
    """

    mocker.patch.object(demisto, 'params', return_value=DEMISTO_PARAMS)
    mocker.patch.object(demisto, 'args', return_value={})
    last_run = mocker.patch.object(demisto, 'getLastRun', return_value={})
    incidents = mocker.patch.object(demisto, 'incidents')

    with requests_mock.Mocker() as m:
        m.get(f'{URL}?{FIRST_REQUESTS_PARAMS}', json=util_load_json('test_data/events.json'))
        m.get(f'{URL}?{SECOND_REQUESTS_PARAMS}', json={})

        from JiraSIEM import main
        main()

    assert last_run.return_value.get('from') == calculate_next_run(incidents.call_args[0][0][0].get('occurred')[:-1])
    assert not last_run.return_value.get('next_time')
    assert last_run.return_value.get('offset') == 0
    assert incidents.call_args[0][0][0].get('name') == f'JiraSIEM - User Changed - 3'


@freeze_time('2022-04-14T00:00:00Z')
def test_fetch_events_no_incidents(mocker):
    """
    Given
        - raw response of the http request
    When
        - fetching incidents
    Then
        - check the number of incidents that are being created
        check that the time in last_run is the on of the latest incident
    """

    mocker.patch.object(demisto, 'params', return_value=DEMISTO_PARAMS)
    mocker.patch.object(demisto, 'args', return_value={})
    last_run = mocker.patch.object(demisto, 'getLastRun', return_value={})
    incidents = mocker.patch.object(demisto, 'incidents')

    with requests_mock.Mocker() as m:
        m.get(f'{URL}?{FIRST_REQUESTS_PARAMS}', json={})

        from JiraSIEM import main
        main()

    assert not last_run.return_value.get('from')
    assert last_run.return_value.get('offset') == 0
    assert not incidents.call_args


@freeze_time('2022-04-14T00:00:00Z')
def test_fetch_events_max_fetch_set_to_one(mocker):
    """
    Given
        - raw response of the http request
    When
        - fetching incidents
    Then
        - check the number of incidents that are being created
        check that the time in last_run is the on of the latest incident
    """
    params = DEMISTO_PARAMS
    params['max_fetch'] = 1
    mocker.patch.object(demisto, 'params', return_value=params)
    mocker.patch.object(demisto, 'args', return_value={})
    last_run = mocker.patch.object(demisto, 'getLastRun', return_value={})
    incidents = mocker.patch.object(demisto, 'incidents')

    with requests_mock.Mocker() as m:
        m.get(f'{URL}?{FIRST_REQUESTS_PARAMS}', json=util_load_json('test_data/events.json'))
        m.get(f'{URL}?{SECOND_REQUESTS_PARAMS}', json={})

        from JiraSIEM import main
        main()

    assert not last_run.return_value.get('from')
    assert last_run.return_value.get('next_time') == '2022-04-12T18:45:42.968'
    assert last_run.return_value.get('offset') == 1
    assert incidents.call_args[0][0][0].get('name') == f'JiraSIEM - User Changed - 3'

