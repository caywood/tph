from collections import Counter, OrderedDict

from sqlalchemy.orm import contains_eager, eagerload

from gtfs.entity import *

import math
from numpy import median, inf

def get_last_stop_id(schedule, trip):
    q = schedule.session.query(StopTime.stop_id)
    q = q.filter(StopTime.trip == trip)
    q = q.order_by(StopTime.stop_sequence.desc()).limit(1)
    return q.scalar()


def get_last_stop_name(schedule, trip):
    q = schedule.session.query(Stop.stop_name)
    q = q.join(StopTime)
    q = q.filter(StopTime.trip == trip)
    q = q.order_by(StopTime.stop_sequence.desc()).limit(1)
    return q.scalar()

def find_interval(intervals, val):
    # returns index of interval corresponding to time value passed in. 
    # returns -1 for times before first interval or after last interval
    arrival_hours = math.fmod(val / 3600., 24.)
    
    intervalidx = -1
    for j in range(len(intervals)-1):
        if (intervals[j] <= arrival_hours < intervals[j+1]):
            intervalidx = j
            break
    return intervalidx

def find_service(schedule, target_date, intervals, target_routes,
                 target_stopid, override_headsign=False,
                 override_direction=False,
                 direction_0_routes=[], direction_1_routes=[],
                 direction_0_terminals=[], direction_1_terminals=[]):

    #TODO: it would be good to validate that the given stop and routes exist.
    
    periods = schedule.service_for_date(target_date)
    
    # combine stop with its parent (if any) and children of parent
    target_stop = Stop.query.filter_by(stop_id=target_stopid).one()
    if target_stop.parent is not None:
        target_stop = target_stop.parent
    target_stops = [target_stop] + target_stop.child_stations

    # identify which routes use frequency, and which use stoptimes
    frequency_routes = []
    for route_id in target_routes:
        if Trip.query.filter(Trip.route_id == route_id).first().uses_frequency:
            frequency_routes.append(route_id)
    all_routes = target_routes
    stoptime_routes = set(target_routes) - set(frequency_routes)

    # initialize results tables
    results_temp = {}
    intervallist_0 = []
    intervallist_1 = []
    for i in range(len(intervals)):
        intervallist_0.append([])
        intervallist_1.append([])
    spacing_0 = [inf] * len(intervals)
    spacing_1 = [inf] * len(intervals)
    worstspacing_0 = [inf] * len(intervals)
    worstspacing_1 = [inf] * len(intervals)
    
    # process a stoptime, storing data for its associated route
    def process_stoptime(stoptime, surrogate_time=None):
        route = stoptime.trip.route
        route_id = route.route_id

        if route_id not in results_temp:
            results_temp[route_id] = {'route_color': route.route_color,
                                      'route_type': route.route_type,
                                      'route_name': route.route_short_name or \
                                      route.route_long_name or route.route_id,
                                      'headsigns_0': Counter(),
                                      'count_0': Counter(),
                                      'timelist_0': [],
                                      'headsigns_1': Counter(),
                                      'count_1': Counter(),
                                      'timelist_1': []}

        trip = stoptime.trip
        final_time = (surrogate_time or stoptime.arrival_time.val)

        if route_id in direction_0_routes or \
               get_last_stop_id(schedule, trip) in direction_0_terminals or \
               (trip.direction_id == 0 and not override_direction):
            count = results_temp[route_id]['count_0']
            headsigns = results_temp[route_id]['headsigns_0']
            timelist = results_temp[route_id]['timelist_0']
        elif route_id in direction_1_routes or \
                 get_last_stop_id(schedule, trip) in direction_1_terminals or \
                 (trip.direction_id == 1 and not override_direction):
            count = results_temp[route_id]['count_1']
            headsigns = results_temp[route_id]['headsigns_1']
            timelist = results_temp[route_id]['timelist_1']            
        else:
            raise Exception("No direction available for trip %s on route %s." % (trip.trip_id, route_id))

        # record time
        timelist.append(final_time)

        # sort into intervals
        intervalidx = find_interval(intervals, final_time)
        if intervalidx != -1:
            count[intervalidx] += 1
            if override_headsign or (trip.trip_headsign is None and \
                                     stoptime.stop_headsign is None):
                headsign = get_last_stop_name(schedule, trip)
            else:
                headsign = trip.trip_headsign or stoptime.stop_headsign
            headsigns[headsign] += 1

    # iterate over stoptime routes           
    if len(stoptime_routes) > 0:
        st = StopTime.query
        st = st.filter(StopTime.stop.has(
            Stop.stop_id.in_([stop.stop_id for stop in target_stops])))
        st = st.join(Trip)
        st = st.join(Route)
        st = st.filter(Trip.service_id.in_(periods))
        st = st.filter(Route.route_id.in_(target_routes))
        st = st.options(contains_eager('trip'), contains_eager('trip.route'))
        st = st.order_by(StopTime.arrival_time.asc())

        for stoptime in st.all():
            process_stoptime(stoptime)
                        
    # iterate over frequency routes           
    if len(frequency_routes) > 0:
        st = StopTime.query
        st = st.filter(StopTime.stop.has(
            Stop.stop_id.in_([stop.stop_id for stop in target_stops])))
        st = st.join(Trip)
        st = st.join(Route)
        st = st.filter(Trip.service_id.in_(periods))
        st = st.filter(Route.route_id.in_(frequency_routes))
        st = st.options(contains_eager('trip'), contains_eager('trip.route'),
                        eagerload('trip.frequencies'))
        st = st.order_by(StopTime.arrival_time.asc())

        for exemplar_stoptime in st.all():
            frequencies = exemplar_stoptime.trip.frequencies
            offset = exemplar_stoptime.elapsed_time
            for frequency in frequencies:
                for trip_time in frequency.trip_times:
                    process_stoptime(exemplar_stoptime, trip_time + offset)

    results = OrderedDict()

    # bin over intervals
    for route_id in all_routes:
        if route_id not in results_temp:
            raise Exception("No data generated for route_id %s. Does it exist in the feed?" % route_id)
        results[route_id] = results_temp[route_id]
        r = results[route_id]
        #r['bins_0'] = [r['count_0'].get(x, 0) for x in range(0, 24)]
        #r['bins_1'] = [r['count_1'].get(x, 0) for x in range(0, 24)]
        r['bins_0'] = [r['count_0'].get(x, 0) for x in range(len(intervals)-1)]
        r['bins_1'] = [r['count_1'].get(x, 0) for x in range(len(intervals)-1)]

    # A 6:05 stop time with a next time of 6:25 is stored under the interval containing 6:05 --
    # If the interval is 6-7, the idea is that between 6 and 7 your next bus wait time will be 20 minutes 
    #
    # If there are buses at 12:00 and 12:20, 12-1 should show as 20 minutes - infinity minutes
    #
    # MSC eventually convert frequency routes to use the frequencies directly as intervals
    last_time = -1;
    for final_time in r['timelist_0']:
        if last_time != -1:
            intervalidx = find_interval(intervals,last_time)
            if intervalidx != -1:
                intervallist_0[intervalidx].append((final_time - last_time) / 60)
        last_time = final_time
    for ival in range(len(intervallist_0)):
        if len(intervallist_0[ival]) > 0:
            spacing_0[ival] = median(intervallist_0[ival])
            worstspacing_0[ival] = max(intervallist_0[ival])

    last_time = -1;
    for final_time in r['timelist_1']:
        if last_time != -1:
            intervalidx = find_interval(intervals,last_time)
            if intervalidx != -1:
                intervallist_1[intervalidx].append((final_time - last_time) / 60)
        last_time = final_time
    for ival in range(len(intervallist_1)):
        if len(intervallist_1[ival]) > 0:
            spacing_1[ival] = median(intervallist_1[ival])
            worstspacing_1[ival] = max(intervallist_1[ival])

    return (results, target_stop.stop_name, r['timelist_0'], spacing_0, worstspacing_0, r['timelist_1'], spacing_1, worstspacing_1)
