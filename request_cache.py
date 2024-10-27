"""
File name: request_cache.py
Author: Luigi Saetta
Date last modified: 2024-10-21
Python Version: 3.11

Description:
    This file provide a class to handle a cache with all the requests
    more frequently mad, in NL, and the resulting SQL code

Inspired by:
   

Usage:
    Import this module into other scripts to use its functions. 
    Example:


License:
    This code is released under the MIT License.

Notes:
    This is a part of a set of demos showing how to build a SQL Agent
    for Text2SQL taks

Warnings:
    This module is in development, may change in future versions.
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
            # add sql to cache (fix bug 27/10/2024)
            self.cache[request_nl]["sql"] = sql_query
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
