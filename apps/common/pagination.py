from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """Project-wide default pagination.

    `?page=2&page_size=24` — page_size is client-adjustable (capped) so the
    search-results grid and admin tables can each ask for what fits their
    layout without needing a second pagination class.
    """

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 60

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
