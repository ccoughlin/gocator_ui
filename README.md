# Gocator 20x0 User Interface

This is a basic web interface to control [Gocator 20x0](http://www.lmi3d.com/product/gocator-family) 3D laser profilers through the [gocator_profiler](https://github.com/ccoughlin/gocator_profiler) console application.  Just like the console app it's probably of limited interest to anyone not me.  Or at least anyone not working on a Gocator laser profiling application, anyway.

The web interface allows the user to configure the laser profiling (triggering, scans per second, etc.) and to download the 3D profile data and/or receive an image of the data plotted as a color-mapped scatter plot (have a look at the console app's [Plotter](https://github.com/ccoughlin/gocator_profiler/blob/master/gocator_plotter.py) for 3D surface plots of the data).

## Requirements
* [Python](http://www.python.org)
* [NumPy](http://www.numpy.org)
* [SciPy](http://www.scipy.org/)
* [matplotlib](http://www.matplotlib.org)
* [Flask](http://flask.pocoo.org/)
* [gocator_profiler](https://github.com/ccoughlin/gocator_profiler)
* [Tornado](http://www.tornadoweb.org/en/stable/) (optional but recommended)