#!/usr/bin/env python3
"""Compile basic statistics of FPC nominations and generate line charts.

This little program compiles basic statistics of candidates for featured
picture status (FPC) on Wikimedia Commons, especially the success rate
for every year.  All data are automatically derived from the candidate
archive categories.  The program prints a wikitext table with the results
and generates simple SVG line charts which illustrate the development
over the years.

The program is primarily a proof of concept.  It demonstrates how easy
it is to generate statistics based on the candidate archive categories.
Therefore the coding style is deliberately rather pedestrian.
Written for/tested with Python 3.14 and Pywikibot 11 on Linux and macOS.

Copyright © 2026 Roman Eisele.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# Imports from the Python Standard Library
from typing import Final
import sys
import datetime
import pathlib
import re

# Third-party imports
import pywikibot
import pygal


# CONSTANTS

# Time frame
NOW: Final[datetime.datetime] = datetime.datetime.now(datetime.timezone.utc)
DATE: Final[str] = NOW.strftime('%Y-%m-%d')
MIN_YEAR: Final[int] = 2019
MAX_YEAR: Final[int] = NOW.year

# Customized chart colours
CHART_STYLE_WITH_TOTAL: Final[pygal.style.Style] = pygal.style.Style(
    # Change colours to match the specific nomination results:
    colors=(
        '#03A9F4', '#3F51B5', '#009688', '#FFC107', '#F44336',
        '#9C27B0', '#999999',
    ),
    background='transparent',
    plot_background='transparent',
    guide_stroke_color='rgba(0, 0, 0, 0.33)',
    major_guide_stroke_color='rgba(0, 0, 0, 0.5)',
    title_font_size=18,
    # Pygal defaults to monospaced font families.
    # You can change the font family, but only the fonts listed here:
    #   https://meta.wikimedia.org/wiki/SVG_fonts
    # will actually work on Commons ...
    # font_family='"Noto Sans", "Liberation Sans", sans-serif',
)
CHART_STYLE_WITHOUT_TOTAL: Final[pygal.style.Style] = pygal.style.Style(
    # Use the same colours, but shifted by one because we do not display
    # the total amount/rate of all nominations (either because all
    # nominations are valid or because we are creating a relative diagram
    # so that the total rate would always be 100%):
    colors=('#3F51B5', '#009688', '#FFC107', '#F44336', '#9C27B0', '#999999'),
    background='transparent',
    plot_background='transparent',
    guide_stroke_color='rgba(0, 0, 0, 0.33)',
    major_guide_stroke_color='rgba(0, 0, 0, 0.5)',
    title_font_size=18,
    # font_family='"Noto Sans", "Liberation Sans", sans-serif',
)


# HELPER CLASSES

class NominationsPerYear():
    """The collected nomination data per year."""

    # Type hinting for instance variables (new style)
    successful: int
    unsuccessful: int
    withdrawn: int
    fpxed_fpded: int
    abandoned: int
    valid: int
    total: int

    def __init__(
        self,
        successful: int,
        unsuccessful: int,
        withdrawn: int,
        fpxed_fpded: int,
        abandoned: int,
    ) -> None:
        """Initialize the record and save the values."""
        self.successful = successful
        self.unsuccessful = unsuccessful
        self.withdrawn = withdrawn
        self.fpxed_fpded = fpxed_fpded
        self.abandoned = abandoned
        self.valid = successful + unsuccessful + withdrawn + fpxed_fpded
        self.total = self.valid + abandoned

    @property
    def valid_rate(self) -> float:
        """Return the percentage of valid nominations.

        NB: The rate of valid and abandoned nominations is relative to
        the total count of nominations, all other rates are relative to
        the count of valid nominations.
        """
        try:
            return 100 * self.valid / self.total
        except ZeroDivisionError:
            return 0.0

    @property
    def successful_rate(self) -> float:
        """Return the percentage of successful nominations."""
        try:
            return 100 * self.successful / self.valid
        except ZeroDivisionError:
            return 0.0

    @property
    def unsuccessful_rate(self) -> float:
        """Return the percentage of unsuccessful nominations."""
        try:
            return 100 * self.unsuccessful / self.valid
        except ZeroDivisionError:
            return 0.0

    @property
    def withdrawn_rate(self) -> float:
        """Return the percentage of withdrawn nominations."""
        try:
            return 100 * self.withdrawn / self.valid
        except ZeroDivisionError:
            return 0.0

    @property
    def fpxed_fpded_rate(self) -> float:
        """Return the percentage of FPXed/FPDed nominations."""
        try:
            return 100 * self.fpxed_fpded / self.valid
        except ZeroDivisionError:
            return 0.0

    @property
    def abandoned_rate(self) -> float:
        """Return the percentage of abandoned nominations."""
        try:
            return 100 * self.abandoned / self.total
        except ZeroDivisionError:
            return 0.0


# MAIN ROUTINE

def main() -> None:
    """The main routine of the program."""

    # Log in if necessary
    print('Setting up and connecting ...')
    try:
        site = pywikibot.Site('commons', 'commons')
    except ConnectionError:
        sys.exit('Can’t connect to the Commons server, aborting.')
    if not site.logged_in():
        site.login()

    # Collect the data
    data_per_year: dict[int, NominationsPerYear] = {}
    for year in range(MIN_YEAR, MAX_YEAR + 1):
        print(f'Collecting data for {year} ...')
        data_per_year[year] = collect_data_for_year(site, year)

    # Build the table
    print('Formatting the data as table ...')
    table = (
        '{| class="wikitable" style="text-align: right"\n'
        f'|+ Candidates for featured picture status (as of {DATE})\n'
        '|-\n'
        '! Year !! Total !! Valid !! Successful !! Unsuccessful '
        '!! Withdrawn !! FPXed/FPDed !! Abandoned\n'
    )
    for year in range(MIN_YEAR, MAX_YEAR + 1):
        table += compile_row_for_year(year, data_per_year[year])
    table += '|}'

    # Print the table
    print()
    print(table)
    print()

    # Create and save the charts
    any_abandoned = any(data.abandoned for data in data_per_year.values())
    print('Creating the chart with absolute numbers ...')
    create_abs_chart(data_per_year, any_abandoned)
    print('Creating the chart with relative numbers ...')
    create_rel_chart(data_per_year, any_abandoned)


# SUBROUTINES

def collect_data_for_year(
    site: pywikibot.site.BaseSite,
    year: int,
) -> NominationsPerYear:
    """Compile the table row with the statistics for a given year.

    Args:
        site: A valid Pywikibot Site object for Commons.
        year: The year the row is about.

    Returns:
        A NominationsPerYear object with the numbers for the given year.
    """
    successful = count_pages_in_category(
        site, f'{year} successful candidates for featured picture status'
    )
    unsuccessful = count_pages_in_category(
        site, f'{year} unsuccessful candidates for featured picture status'
    )
    withdrawn = count_pages_in_category(
        site, f'{year} withdrawn candidates for featured picture status'
    )
    fpxed = count_pages_in_category(
        site, f'{year} FPXed candidates for featured picture status'
    )
    fpded = count_pages_in_category(
        site, f'{year} FPDed candidates for featured picture status'
    )
    abandoned = count_pages_in_category(
        site, f'{year} abandoned candidates for featured picture status'
    )
    return NominationsPerYear(
        successful, unsuccessful, withdrawn, fpxed + fpded, abandoned
    )


def count_pages_in_category(
    site: pywikibot.site.BaseSite,
    category_name: str,
) -> int:
    """Return the number of pages in a given category.

    Args:
        site: A valid Pywikibot Site object for Commons.
        category_name: The name of the category, without namespace prefix.

    Returns:
        The count of pages in the category if it exists, else 0.
    """
    category = pywikibot.Category(site, category_name)
    try:
        count = category.categoryinfo['pages']
        assert isinstance(count, int)
    except pywikibot.exceptions.PageRelatedError:
        count = 0
    return count


def compile_row_for_year(year: int, data: NominationsPerYear) -> str:
    """Compile the table row with the statistics for a given year.

    Args:
        year: The year the row is about.
        data: A NominationsPerYear with the numbers for that year.

    Returns:
        A wikitext table row with the numbers for the given year.
    """
    valid = format_abs_rel(data.valid, data.valid_rate)
    successful = format_abs_rel(data.successful, data.successful_rate)
    unsuccessful = format_abs_rel(data.unsuccessful, data.unsuccessful_rate)
    withdrawn = format_abs_rel(data.withdrawn, data.withdrawn_rate)
    fpxed_fpded = format_abs_rel(data.fpxed_fpded, data.fpxed_fpded_rate)
    abandoned = format_abs_rel(data.abandoned, data.abandoned_rate)
    return (
        '|-\n'
        f'! {year}\n'
        f'| {data.total} || {valid} '
        f'|| {successful} || {unsuccessful} '
        f'|| {withdrawn} || {fpxed_fpded} || {abandoned}\n'
    )


def format_abs_rel(count: int, percent: float) -> str:
    """Format a count and the corresponding percentage."""
    return f'{count} = {percent:0.2f}\u00A0%'


def create_abs_chart(
    data_per_year: dict[int, NominationsPerYear],
    any_abandoned: bool,
) -> None:
    """Create and save a line chart with the absolute numbers per year.

    Args:
        data_per_year: A dictionary using the years as keys
            and the as NominationsPerYear objects as values.
        any_abandoned: Are there any abandoned nominations?
            If False, all nominations are valid.
    """
    # Sort the data
    sorted_data = [
        data_per_year[year] for year in range(MIN_YEAR, MAX_YEAR + 1)
    ]
    if any_abandoned:
        total_per_year = [data.total for data in sorted_data]
    valid_per_year = [data.valid for data in sorted_data]
    successful_per_year = [data.successful for data in sorted_data]
    unsuccessful_per_year = [data.unsuccessful for data in sorted_data]
    withdrawn_per_year = [data.withdrawn for data in sorted_data]
    fpx_fpd_per_year = [data.fpxed_fpded for data in sorted_data]
    if any_abandoned:
        abandoned_per_year = [data.abandoned for data in sorted_data]

    # Define the chart
    style = (
        CHART_STYLE_WITH_TOTAL if any_abandoned else CHART_STYLE_WITHOUT_TOTAL
    )
    chart = pygal.Line(style=style, include_x_axis=True)
    chart.title = (
        'Candidates for featured picture status per year – '
        'absolute numbers'
    )
    chart.x_labels = list(map(str, range(MIN_YEAR, MAX_YEAR + 1)))

    # Add the data
    if any_abandoned:
        chart.add('Total', total_per_year)
        chart.add('Valid', valid_per_year)
    else:  # The lines would be congruent, so draw just one.
        chart.add('Total/valid', valid_per_year)
    chart.add('Successful', successful_per_year)
    chart.add('Unsuccessful', unsuccessful_per_year)
    chart.add('Withdrawn', withdrawn_per_year)
    chart.add('FPXed/FPDed', fpx_fpd_per_year)
    if any_abandoned:
        chart.add('Abandoned', abandoned_per_year)
    # Else: omit the line because it would be congruent with the abscissa.

    # Render and save the chart as SVG file
    render_and_save_chart(chart, 'fpc_nominations_per_year.svg')


def create_rel_chart(
    data_per_year: dict[int, NominationsPerYear],
    any_abandoned: bool,
) -> None:
    """Create and save a line chart with the success rate etc. per year.

    Args:
        data_per_year: A dictionary using the years as keys
            and the as NominationsPerYear objects as values.
        any_abandoned: Are there any abandoned nominations?
            If False, all nominations are valid.
    """
    # Sort the data
    sorted_data = [
        data_per_year[year] for year in range(MIN_YEAR, MAX_YEAR + 1)
    ]
    # We omit the percentage of all nominations, it’s always 100 %.
    valid_per_year = [data.valid_rate for data in sorted_data]
    successful_per_year = [data.successful_rate for data in sorted_data]
    unsuccessful_per_year = [data.unsuccessful_rate for data in sorted_data]
    withdrawn_per_year = [data.withdrawn_rate for data in sorted_data]
    fpx_fpd_per_year = [data.fpxed_fpded_rate for data in sorted_data]
    if any_abandoned:
        abandoned_per_year = [data.abandoned_rate for data in sorted_data]

    # Define the chart
    chart = pygal.Line(style=CHART_STYLE_WITHOUT_TOTAL, include_x_axis=True)
    chart.title = (
        'Candidates for featured picture status per year – '
        'success rate'
    )
    chart.x_labels = list(map(str, range(MIN_YEAR, MAX_YEAR + 1)))
    chart.value_formatter = lambda y: f'{round(y)} %'  # Format y values.

    # Add the data
    chart.add('Valid', valid_per_year)
    chart.add('Successful', successful_per_year)
    chart.add('Unsuccessful', unsuccessful_per_year)
    chart.add('Withdrawn', withdrawn_per_year)
    chart.add('FPXed/FPDed', fpx_fpd_per_year)
    if any_abandoned:
        chart.add('Abandoned', abandoned_per_year)
    # Else: omit the line because it would be congruent with the abscissa.

    # Render and save the chart as SVG file
    render_and_save_chart(chart, 'fpc_success_rate_per_year.svg')


def render_and_save_chart(chart: pygal.Graph, filename: str) -> None:
    """Render the chart as SVG data and save them to a file."""
    # Render the chart
    svg_data = chart.render(
        is_unicode=True,     # We need an Unicode string, not bytes.
        pretty_print=False,  # Set to True if you want to edit the file.
        no_prefix=True,      # Don’t add ID prefix to every CSS definition.
    )
    # We must disable all <script> tags (which e.g. power the beautiful
    # rollover labels) because Commons doesn’t allow to upload SVG files
    # with <script> tags.  We just comment out the tags, so people can
    # enable them if they want to study the chart, use it on a website, etc.
    svg_data = re.sub(
        r'((?:<script\b(?:(?:[^>]*[^/>])?>.*?</script>|[^>]*/>)\s*)+)',
        r'<!--\1-->',
        svg_data,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # With ‘no_prefix=True’, pygal generates an empty ID attribute
    # for the SVG root element; that’s invalid, so remove the attribute.
    svg_data = svg_data.replace(' id=""', '')

    # Save the chart
    file_path = pathlib.Path(filename)
    try:
        file_path.write_text(
            svg_data, encoding='utf-8', errors='strict', newline='\n'
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f'Cound not save the chart to a SVG file: {exc}.')
    else:
        print(
            'The chart was saved to your current working directory '
            f'as ‘{filename}’.'
        )


# THE OBLIGATORY IDIOM

if __name__ == '__main__':
    main()


# END OF FILE
