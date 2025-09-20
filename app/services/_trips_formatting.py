"""
Trip formatting for export
"""


class _Formatter:
    """
    Trip Formatter
    """

    def __init__(self):
        self._FORMATS = ['html']
        self._FORMATTERS = {
            'html': self._format_html
        }

    def format(
        self,
        trip_details: dict,
        itinerary: list,
        type: str = 'html'
    ) -> str:
        if type in self._FORMATS:
            return self._FORMATTERS[type](trip_details, itinerary)
        else:
            raise ValueError(f"Unsupported format type: {type}")

    def _format_html(self, trip_details: dict, itinerary: list) -> str:
        """
        Format trip and itinerary data into a styled HTML structure
        """
        trip_header_html = self._process_details_html(trip_details)
        itinerary_html = self._process_itinerary_html(itinerary)

        return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8" />
                <title>{trip_details.get("name", "Trip Itinerary")}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f8f9fa;
                        color: #333;
                    }}
                    .trip-header {{
                        background: #0077cc;
                        color: white;
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 30px;
                    }}
                    .trip-header h1 {{
                        margin: 0;
                        font-size: 2rem;
                    }}
                    .trip-header p {{
                        margin: 5px 0;
                    }}
                    .itinerary {{
                        margin-top: 20px;
                    }}
                    .item {{
                        background: white;
                        padding: 15px;
                        margin-bottom: 15px;
                        border-radius: 10px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }}
                    .item h2 {{
                        margin-top: 0;
                        color: #0077cc;
                    }}
                    .meta {{
                        font-size: 0.9rem;
                        color: #666;
                    }}
                    a {{
                        color: #0077cc;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                {trip_header_html}
                <div class="itinerary">
                    <h1>Itinerary</h1>
                    {itinerary_html}
                </div>
            </body>
            </html>
        """

    def _process_itinerary_html(self, itinerary: list) -> str:
        """
        Process itinerary into styled HTML cards
        """
        html_content = ""
        for item in itinerary:
            html_content += f"""
            <div class="item">
                <h2>{item.get('name', 'No Name')}</h2>
                <p class="meta">Type: {item.get('type', 'N/A')}</p>
                {f"<p><b>Start:</b> {item['start_time']}</p>" if item.get("start_time") else ""}
                {f"<p><b>End:</b> {item['end_time']}</p>" if item.get("end_time") else ""}
                {f"<p><b>Cost:</b> {item['cost_amount']} {item['cost_currency']}</p>" if item.get("cost_amount") and item.get("cost_currency") else ""}
                {f"<p><b>Link:</b> <a href='{item['link']}'>{item['link']}</a></p>" if item.get("link") else ""}
                {f"<p><b>Notes:</b> {item['notes']}</p>" if item.get("notes") else ""}
            </div>
            """
        return html_content



trip_formatter = _Formatter()
