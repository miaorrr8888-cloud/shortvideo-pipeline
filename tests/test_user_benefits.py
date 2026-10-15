from pathlib import Path
import importlib.util, unittest, tempfile, subprocess, sys, json, zipfile, io, struct, os
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

from shortvideo_pipeline import Pipeline, TopicBrief
from shortvideo_pipeline.llm.mock import MockProvider
from shortvideo_pipeline.output import write_package

class OutputProtection(unittest.TestCase):
    def test_repeat_export_preserves_first_output(self):
        package=Pipeline(MockProvider()).run(TopicBrief.from_dict({'title':'Synthetic output','duration_target':60}))
        with tempfile.TemporaryDirectory() as d:
            first=Path(write_package(package,d)); marker=first/'preserve.txt'; marker.write_text('keep')
            second=Path(write_package(package,d)); self.assertNotEqual(first,second); self.assertEqual(marker.read_text(),'keep')
    def test_dry_run_cannot_be_overridden_by_cloud_provider(self):
        from argparse import Namespace
        from shortvideo_pipeline.cli import _make_pipeline
        with tempfile.TemporaryDirectory() as d:
            pipeline=_make_pipeline(Namespace(env=str(Path(d)/'missing.env'),dry_run=True,provider='siliconflow'))
            self.assertEqual(pipeline.settings.llm_provider,'mock')
    def test_unsafe_slug_rejected(self):
        package=Pipeline(MockProvider()).run(TopicBrief.from_dict({'title':'Synthetic output','duration_target':60})); package.slug='../escape'
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): write_package(package,d)
    def test_boolean_duration_and_bad_pains_rejected(self):
        for fields in [{'duration_target':True},{'pain_points':'not a list'},{'title':'   '}]:
            data={'title':'Demo','duration_target':60}; data.update(fields)
            with self.assertRaises(ValueError): TopicBrief.from_dict(data)

if __name__=="__main__": unittest.main()
