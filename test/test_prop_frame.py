import sys
from collections import Iterable
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.setmethod
def test_create_concrete_beam(shayesteh):
    ret = shayesteh.prop_frame.create_concrete_beam('B20X20', 'CONC', 200, 200, 'RMAT', 'RMAT-1', 400)
    assert ret
    shayesteh.SapModel.PropFrame.Delete('B20X20')

@pytest.mark.setmethod
def test_create_concrete_column(shayesteh):
    ret = shayesteh.prop_frame.create_concrete_column('C50X80', 'CONC', 800, 500, 'RMAT', 'RMAT-1', 75, 3, 6, '20d', '10d')
    assert ret
    shayesteh.SapModel.PropFrame.Delete('C50X80')

@pytest.mark.getmethod
def test_get_concrete_rectangular_of_type(shayesteh):
    ret = shayesteh.prop_frame.get_concrete_rectangular_of_type()
    assert len(ret) == 112
    assert isinstance(ret, Iterable)

@pytest.mark.setmethod
def test_convert_columns_design_types(shayesteh):
    shayesteh.prop_frame.convert_columns_design_types()
    ret = shayesteh.SapModel.PropFrame.GetRebarColumn("C5016F20")
    assert ret[-2]
    shayesteh.prop_frame.convert_columns_design_types(design=False)
    shayesteh.prop_frame.convert_columns_design_types(columns=['107'])
    ret = shayesteh.SapModel.PropFrame.GetRebarColumn("C5016F20")
    assert ret[-2]
    ret = shayesteh.SapModel.PropFrame.GetRebarColumn("C4512F18")
    assert not ret[-2]


if __name__ == '__main__':
    from pathlib import Path
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    SapModel = etabs.SapModel
