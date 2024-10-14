"""
RequestCache
"""


class RequestCache:
    """
    In memory cache for the request to be translated in SQL

    # Dato: {request_nl: {'sql': sql, 'count': 0, 'success': 0, 'failures': 0, 'total_time': 0}}
    """

    def __init__(self):
        self.cache = {}

    def add_to_cache(self, request_nl, sql_query, success=True, generation_time=None):
        """
        add a pair (user_request, sql) to the cache, together with stats
        """
        if request_nl not in self.cache:
            self.cache[request_nl] = {
                "sql": sql_query,
                "count": 0,
                "success": 0,
                "failures": 0,
                "total_time": 0,
            }

        # Aggiornamento delle statistiche
        self.cache[request_nl]["count"] += 1
        if success:
            self.cache[request_nl]["success"] += 1
        else:
            self.cache[request_nl]["failures"] += 1

        if generation_time is not None:
            self.cache[request_nl]["total_time"] += generation_time

    def get_request_with_stats(self, request_nl):
        """
        get an entry (with stats)
        """
        if request_nl in self.cache:
            data = self.cache[request_nl]
            avg_time = (
                round(data["total_time"] / data["count"], 2)
                if data["count"] > 0
                else None
            )
            return {
                "sql": data["sql"],
                "total_count": data["count"],
                "success_count": data["success"],
                "failure_count": data["failures"],
                "average_generation_time": str(avg_time),
            }
        return None

    def get_all_stats(self):
        """
        get all stats
        """
        all_stats = {}
        for request_nl in self.cache:
            all_stats[request_nl] = self.get_request_with_stats(request_nl)
        return all_stats
