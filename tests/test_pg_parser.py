import json

import pytest
import pyproj

from eodc_pg_parser.graph import OpenEOProcessGraph
from eodc_pg_parser.pg_schema import *
from tests.conftest import TEST_DATA_DIR, TEST_NODE_KEY

def test_full_parse(process_graph_path):
    parsed_graph_from_file = OpenEOProcessGraph.from_file(process_graph_path)
    parsed_graph_from_json = OpenEOProcessGraph.from_json(json.dumps(json.load(open(process_graph_path, mode="r"))))
    assert isinstance(parsed_graph_from_file, OpenEOProcessGraph)
    assert parsed_graph_from_file == parsed_graph_from_json

def test_from_json_constructor():
    flat_process_graph = json.load(open(TEST_DATA_DIR / "graphs"/ "fit_rf_pg_0.json", mode="r"))
    parsed_graph = OpenEOProcessGraph.from_json(json.dumps(flat_process_graph))
    assert isinstance(parsed_graph, OpenEOProcessGraph)

def test_data_types_explicitly():
    flat_process_graph = json.load(open(TEST_DATA_DIR / "graphs"/ "fit_rf_pg_0.json", mode="r"))
    nested_process_graph = OpenEOProcessGraph._unflatten_raw_process_graph(
        flat_process_graph
    )
    parsed_process_graph = OpenEOProcessGraph._parse_datamodel(nested_process_graph)
    assert isinstance(parsed_process_graph, ProcessGraph)
    assert isinstance(parsed_process_graph.process_graph["root"], ProcessNode)
    assert isinstance(
        parsed_process_graph.process_graph["root"].arguments["model"], ResultReference
    )
    assert isinstance(
        parsed_process_graph.process_graph["root"].arguments["model"].node,
        ProcessNode,
    )


def test_bounding_box(get_process_graph_with_args):
    pg = get_process_graph_with_args(
        {
            'spatial_extent': {
                'west': 0,
                'east': 10,
                'south': 0,
                'north': 10,
                'crs': "EPSG:2025",
            }
        }
    )
    parsed_arg = (
        ProcessGraph.parse_obj(pg)
        .process_graph[TEST_NODE_KEY]
        .arguments["spatial_extent"]
    )
    assert isinstance(parsed_arg, BoundingBox)
    assert isinstance(parsed_arg.crs, pyproj.CRS)
    assert parsed_arg.crs == 'EPSG:2025'


def test_bounding_box_no_crs(get_process_graph_with_args):
    pg = get_process_graph_with_args(
        {'spatial_extent': {'west': 0, 'east': 10, 'south': 0, 'north': 10, 'crs': ""}}
    )
    parsed_arg = (
        ProcessGraph.parse_obj(pg)
        .process_graph[TEST_NODE_KEY]
        .arguments["spatial_extent"]
    )
    assert isinstance(parsed_arg, BoundingBox)
    assert isinstance(parsed_arg.crs, pyproj.CRS)
    assert parsed_arg.crs == DEFAULT_CRS


def test_bounding_box_with_faulty_crs(get_process_graph_with_args):
    pg = get_process_graph_with_args(
        {
            'spatial_extent': {
                'west': 0,
                'east': 10,
                'south': 0,
                'north': 10,
                'crs': "hello",
            }
        }
    )
    with pytest.raises(pyproj.exceptions.CRSError):
        ProcessGraph.parse_obj(pg).process_graph[TEST_NODE_KEY].arguments[
            "spatial_extent"
        ]


def test_geojson(get_process_graph_with_args):
    # TODO: Generate arbitrary GeoJSONs for testing using something like this hypothesis extension: https://github.com/mapbox/hypothesis-geojson
    argument = {
        'geometries': {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": 0,
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [102.0, 0.5]},
                    "properties": {"prop0": "value0"},
                }
            ],
            "crs": "EPSG:2025",
        }
    }
    pg = get_process_graph_with_args(argument)
    parsed_arg = (
        ProcessGraph.parse_obj(pg).process_graph[TEST_NODE_KEY].arguments["geometries"]
    )
    assert isinstance(parsed_arg, GeoJson)
    assert parsed_arg.crs == 'EPSG:2025'


def test_geojson_faulty_crs(get_process_graph_with_args):
    argument = {
        'geometries': {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": 0,
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [102.0, 0.5]},
                    "properties": {"prop0": "value0"},
                }
            ],
            "crs": "hello",
        }
    }
    pg = get_process_graph_with_args(argument)
    with pytest.raises(pyproj.exceptions.CRSError):
        ProcessGraph.parse_obj(pg).process_graph[TEST_NODE_KEY].arguments["geometries"]


def test_geojson_without_crs(get_process_graph_with_args):
    argument = {
        'geometries': {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": 0,
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [102.0, 0.5]},
                    "properties": {"prop0": "value0"},
                }
            ],
            "crs": "",
        }
    }
    pg = get_process_graph_with_args(argument)
    parsed_arg = (
        ProcessGraph.parse_obj(pg).process_graph[TEST_NODE_KEY].arguments["geometries"]
    )
    assert isinstance(parsed_arg, GeoJson)
    assert parsed_arg.crs == DEFAULT_CRS


def test_jobid(get_process_graph_with_args):
    argument = {'job_id': 'jb-4da83382-8f8e-4153-8961-e15614b04185'}
    pg = get_process_graph_with_args(argument)
    parsed_arg = (
        ProcessGraph.parse_obj(pg).process_graph[TEST_NODE_KEY].arguments["job_id"]
    )
    assert isinstance(parsed_arg, JobId)


def test_output_format(get_process_graph_with_args):
    argument = {'output_format': 'GTiff'}
    pg = get_process_graph_with_args(argument)
    parsed_arg = (
        ProcessGraph.parse_obj(pg).process_graph[TEST_NODE_KEY].arguments["output_format"]
    )
    assert isinstance(parsed_arg, OutputFormat)


def test_uri(get_process_graph_with_args):
    argument = {'uri': 'http://uri.com/'}
    pg = get_process_graph_with_args(argument)
    parsed_arg = ProcessGraph.parse_obj(pg).process_graph[TEST_NODE_KEY].arguments["uri"]
    assert isinstance(parsed_arg, URI)


def test_temporal_interval(get_process_graph_with_args):
    argument1 = {'temporal_interval': ['1990-01-01T12:00:00', '20:00:00']}
    pg = get_process_graph_with_args(argument1)
    parsed_arg = (
        ProcessGraph.parse_obj(pg)
        .process_graph[TEST_NODE_KEY]
        .arguments["temporal_interval"]
    )
    assert isinstance(parsed_arg, TemporalInterval)
    assert isinstance(parsed_arg.__root__[0], DateTime)
    assert isinstance(parsed_arg.__root__[1], Time)

    argument2 = {'temporal_interval': ['1990-01-01T12:00:00', '20:00:00']}
    pg = get_process_graph_with_args(argument2)
    parsed_arg = (
        ProcessGraph.parse_obj(pg)
        .process_graph[TEST_NODE_KEY]
        .arguments["temporal_interval"]
    )
    assert isinstance(parsed_arg, TemporalInterval)
    assert isinstance(parsed_arg.__root__[0], DateTime)
    assert isinstance(parsed_arg.__root__[1], Time)


def test_duration(get_process_graph_with_args):
    argument = {'duration': 'P1Y1M1DT2H'}
    pg = get_process_graph_with_args(argument)
    parsed_arg = (
        ProcessGraph.parse_obj(pg).process_graph[TEST_NODE_KEY].arguments["duration"]
    )
    assert isinstance(parsed_arg, Duration)
