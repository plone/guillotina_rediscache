from guillotina import configure
from guillotina import schema
from guillotina.behaviors.instance import AnnotationBehavior
from guillotina.content import Item
from guillotina.interfaces import IItem
from zope.interface import Interface


class IMarkerBehavior1(Interface):
    pass


class ITestBehavior1(Interface):
    foobar = schema.TextLine()


@configure.behavior(
    title="",
    provides=ITestBehavior1,
    marker=IMarkerBehavior1,
    for_="guillotina.interfaces.IResource")
class TestBehavior1(AnnotationBehavior):
    pass


class ITestContent1(IItem):
    foobar1 = schema.TextLine()


@configure.contenttype(
    type_name="TestContent1",
    schema=ITestContent1,
    behaviors=[
        "guillotina.behaviors.dublincore.IDublinCore",
        "measures.configuration.ITestBehavior1"
    ])
class TestContent1(Item):
    pass
