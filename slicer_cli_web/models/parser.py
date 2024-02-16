import json
from os.path import dirname, join

import yaml
from girder.models.file import File
from jsonschema import validate

from ..cli_utils import as_model
from .json_to_xml import json_to_xml

with open(join(dirname(__file__), 'schema.json')) as f:
    json_schema = json.load(f)


def _parse_xml_desc(item, user, xml):
    meta_data = {
        'xml': xml
    }

    # parse and inject advanced meta data and description
    clim = as_model(xml)
    item['description'] = '**%s**\n\n%s' % (clim.title, clim.description)

    if clim.category:
        meta_data['category'] = clim.category
    if clim.version:
        meta_data['version'] = clim.version
    if clim.license:
        meta_data['license'] = clim.license
    if clim.contributor:
        meta_data['contributor'] = clim.contributor
    if clim.acknowledgements:
        meta_data['acknowledgements'] = clim.acknowledgements

    if clim.documentation_url:
        fileModel = File()
        fileModel.createLinkFile('Documentation', item, 'item',
                                 clim.documentation_url,
                                 user, reuseExisting=True)
    return meta_data


def parse_xml_desc(item, desc, user):
    try:
        return _parse_xml_desc(item, user, desc['xml'])
    except Exception as exc:
        raise Exception('Failed to parse xml (error %s), xml: """%s"""' % (exc, desc['xml']))


def _parse_json_desc(item, user, data):
    validate(data, schema=json_schema)
    xml = json_to_xml(data)
    return _parse_xml_desc(item, user, xml)


def parse_json_desc(item, desc, user):
    try:
        data = json.loads(desc['json'])
    except Exception as exc:
        raise Exception('Failed to load json (error %s), json: """%s"""' % (exc, desc['json']))
    try:
        return _parse_json_desc(item, user, data)
    except Exception as exc:
        raise Exception('Failed to parse json (error %s), json: """%s"""' % (exc, desc['json']))


def parse_yaml_desc(item, desc, user):
    try:
        data = yaml.safe_load(desc['yaml'])
    except Exception as exc:
        raise Exception('Failed to load yaml (error %s), yaml: """%s"""' % (exc, desc['yaml']))
    try:
        return _parse_json_desc(item, user, data)
    except Exception as exc:
        raise Exception('Failed to parse yaml (error %s), yaml: """%s"""' % (exc, desc['yaml']))

def sanitize_and_return_json(res:str):
    '''
    This function tries to parse the given str as json in couple different ways. If the output is still not json or a python dictionary, it raises an error.
    '''
    try:
        res = json.loads(res)
        #This is the form in which we get data back if we use the --json label in singularity inspect
        return res['data']['attributes']['labels']
    except json.decoder.JSONDecodeError as e:
        #If the json label was excluded, we can still parse the labels manually and create a dictionary
        labels= [line for line in res.split('\n')]
        res_dict = {}
        for label in labels:
            key, value = label.split(': ')
            res_dict[key] = value
        return res_dict
    except Exception as e:
        raise Exception(f'Error occured when parsing labels as json {e}')