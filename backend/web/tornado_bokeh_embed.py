from jinja2 import Environment, FileSystemLoader

from tornado.web import RequestHandler

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import server_document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme

from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

env = Environment(loader=FileSystemLoader('templates'))
server_url = "http://localhost:9090/"


class IndexHandler(RequestHandler):
    def get(self):
        print("index ...")
        template = env.get_template('bokeh_embed.html')
        script = server_document(server_url + 'bkapp')
        print(script)
        self.write(template.render(script=script, template="Tornado"))
        # self.write(html_content)


def modify_doc(doc):
    df = sea_surface_temperature.copy()
    source = ColumnDataSource(data=df)

    plot = figure(x_axis_type='datetime', y_range=(0, 25), y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line('time', 'temperature', source=source)

    def callback(attr, old, new):
        if new == 0:
            data = df
        else:
            data = df.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource(data=data).data

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change('value', callback)

    doc.add_root(column(slider, plot))

    # doc.theme = Theme(filename="theme.yaml")


bokeh_app = Application(FunctionHandler(modify_doc))

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server(
    {'/bkapp': bokeh_app}, num_procs=1, port=9999,
    extra_patterns=[('/', IndexHandler)]
)
server.start()

if __name__ == '__main__':
    from bokeh.util.browser import view

    print('Opening Tornado app with embedded Bokeh application on ' + server_url)

    server.io_loop.add_callback(view, server_url)
    server.io_loop.start()
