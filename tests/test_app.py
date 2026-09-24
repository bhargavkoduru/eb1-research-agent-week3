from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_standalone_week3_app_renders():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == 'EB-1 Research Agent - Week 3'
    assert any(b.label == 'Start research' for b in app.button)
    assert not app.sidebar.radio
