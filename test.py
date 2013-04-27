__author__ = 'wynand'

import hierarchy


def test_basic():
    widgets = [
        {'type': 'button',
         'text': 'Hello, world',
         'decoration': 'Bevelled'},
        {'type': 'toggle_button',
         'text': 'On or off?',
         'decoration': 'Flat'},
        {'type': 'toggle_button',
         'text': 'Wax on, wax off',
         'decoration': 'Karate Kid'},
        {'type': 'window',
         'title': 'A nice window'}
    ]

    gui = hierarchy.Hierarchy('widget')
    gui.derive('button', 'widget')
    gui.derive('toggle_button', 'button')
    gui.derive('window', 'widget')

    @gui.multimethod(lambda widget: widget['type'], gui)
    def to_string():
        pass

    @to_string.add_method('button')
    def to_string(button):
        return "I am a button with text '{0}' and decoration '{1}'".format(
            button['text'], button['decoration'])

    @to_string.add_method('widget')
    def to_string(widget):
        return "I am a widget of type {0}".format(widget['type'])

    for widget in widgets:
        print to_string(widget)

    @gui.multimethod(lambda widget1, widget2, **kwargs: (widget1['type'], widget2['type']), gui)
    def embed():
        pass

    @embed.add_method(embed.default_dispatch_val)
    def embed(widget_a, widget_b, **kwargs):
        print "Don't know how to embed {0} on {1}".format(to_string(widget_a), to_string(widget_b))

    @embed.add_method(('button', 'window'))
    def embed(button, window, **kwargs):
        print "Embedding {0} on {1} with args {2}".format(to_string(button), to_string(window), kwargs)

    embed(widgets[0], widgets[-1])
    embed(widgets[1], widgets[-1], size=10)
    embed(widgets[2], widgets[-1], side='L')
    embed(widgets[-1], widgets[0])

def test_disambiguation():
    shapes = hierarchy.Hierarchy('shape')
    shapes.derive('rect', 'shape')
    shapes.derive('square', 'rect')

    @shapes.multimethod(lambda s1, s2: (s1, s2))
    def bar():
        pass

    @bar.add_method(['rect', 'shape'])
    def bar(a, b):
        return 'rect-shape'

    @bar.add_method(['shape', 'rect'])
    def bar(a, b):
        return 'shape-rect'

    #print bar('rect', 'rect')

    bar.prefer_method(['rect', 'shape'], ['shape', 'rect'])
    # print bar('rect', 'rect')
    print bar('square', 'rect')