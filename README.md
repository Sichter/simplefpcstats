simplefpcstats
==============

Simple example programs for creating statistics of the [featured picture candidates](https://commons.wikimedia.org/wiki/Commons:Featured_picture_candidates) (FPC) on *[Wikimedia Commons](https://commons.wikimedia.org/)*.  They demonstrate how easily detailed statistics and clear charts can be compiled from the [candidate archive categories](https://commons.wikimedia.org/wiki/Category:Featured_picture_candidate_archives), and can serve as a starting point for your own programs.


What’s the point?
-----------------

*Commons* users have often argued about the development of the [featured pictures](https://commons.wikimedia.org/wiki/Commons:Featured_pictures) (FP) project.  To support their respective positions, they usually referred to statistics that they had collated by hand based on the [FPC log pages](https://commons.wikimedia.org/wiki/Commons:Featured_picture_candidates/Log).  Manually compiling these statistics was a tedious and error-prone task, and when users arrived at different results, it was often difficult to determine the cause of the difference.  Furthermore, the log pages were incomplete, which inevitably impaired the results somewhat.

Thanks to the [candidate archive categories](https://commons.wikimedia.org/wiki/Category:Featured_picture_candidate_archives) introduced in 2026, it is now possible to create such statistics with just a few lines of code, and the results are also much more reliable than manually calculated values.  The example programs show how this works.  You can easily modify the code to create other kinds of statistics.


Who is this for?
----------------

All programs in this repository are primarily intended to serve as proof of concept, as a basis for discussion with interested FPC regulars, and as inspiration for more ambitious programs.  They are targeting interested amateur programmers with little to medium experience.  Therefore, the coding style is deliberately pedestrian, and every code file is self-contained.  Normally this is a bad idea because it leads to repetitions and duplicates information, but it makes it easier to adapt the code for your own projects.


Dependencies
------------

The programs are based on [Pywikibot](https://doc.wikimedia.org/pywikibot/stable/), the most popular Python library for working with [Mediawiki](https://www.mediawiki.org/wiki/MediaWiki) websites like *Commons*.  Of course this is not necessary, you can also communicate directly with the Mediawiki API, especially if you do not want to run a big bot program, but just want to check some pages or categories.  But the programs in this repositry have to be simple, so they just use the ready-made classes and functions from Pywikibot.

The programs utilize [Pygal](https://www.pygal.org/en/stable/) to generate simple SVG charts.  One of the advantages of `pygal` is that it generates charts with beautiful and unobtrusive dynamic elements, e.g. very clear and elegant tooltip labels for the points of a line graph.  This is done with the help of JavaScript.  Unfortunately we must disable all `<script>` tags because *Commons* doesn’t allow to upload SVG files with `<script>` tags.  The result are rather static charts.  We just comment out the `<script>` tags and don’t delete them, so people can uncomment them after downloading a chart if they want to study it in great detail, use it on another website, etc.


Legal stuff
-----------

All code in this repository is free software: you can redistribute it and/or modify it under the terms of the [GNU General Public License](https://www.gnu.org/licenses/gpl-3.0.html) as published by the [Free Software Foundation](https://www.fsf.org/), either version 3 of the License, or (at your option) any later version.  The code is distributed in the hope that it will be useful, but *without any warranty*; see the GNU General Public License for more details.  You should find a copy of the GNU General Public License in this repository.  If not, please see [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/).
