import asyncpg
import base64
import ujson


def dumps(value):
    """
    Serialize the received value using ``json.dumps``.

    :param value: dict
    :returns: str
    """
    if isinstance(value, asyncpg.Record):
        value = dict(value)
    if isinstance(value, dict):
        value['state'] = base64.b64encode(value['state']).decode('ascii')
    return ujson.dumps(value)


def loads(value):
    """
    Deserialize value using ``ujson.loads``.

    :param value: str
    :returns: output of ``json.loads``.
    """
    if value is None:
        return None
    value = ujson.loads(value)
    if isinstance(value, dict):
        if 'state' in value:
            value['state'] = base64.b64decode(value['state'].encode('ascii'))
    return value
