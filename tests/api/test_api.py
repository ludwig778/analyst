from pytest import mark


@mark.api
def test_root_api(client):
    response = client.get('/')
    assert len(response.json().keys()) == 5


@mark.api
def test_assets_list(client):
    response = client.get('/assets/')
    assert len(response.json().get("results")) == 6


@mark.api
def test_indexes_list(client):
    response = client.get('/indexes/')
    assert len(response.json().get("results")) == 2


@mark.api
def test_portfolios_list(client):
    response = client.get('/portfolios/')
    assert len(response.json().get("results")) == 3
