import sys
import eccodes
import numpy as np

from math import floor

from datetime import datetime, timedelta, timezone
from thermofeel.thermofeel import *

def decode_grib(fpath):
    messages = []
    i = 0
    with open(fpath, "rb") as f:
        while True:
            msg = eccodes.codes_any_new_from_file(f)
            if msg is None:
                break

            i += 1
            print("message %d ----------------------------------", i)

            md = dict()

            # decode metadata

            # loop metadata key-values
            # it = eccodes.codes_keys_iterator_new(msg, 'mars')
            # while eccodes.codes_keys_iterator_next(it):
            #     k = eccodes.codes_keys_iterator_get_name(it)
            #     v = eccodes.codes_get_string(msg, k)
            #     print("%s = %s" % (k, v))
            # eccodes.codes_keys_iterator_delete(it)

            # time_l = eccodes.codes_get_long(msg, "time")
            # time_f = eccodes.codes_get_double(msg, "time")

            md['Ni'] = eccodes.codes_get_long(msg, "Ni")
            md['Nj'] = eccodes.codes_get_long(msg, "Nj")

            md["time"] = eccodes.codes_get_long(msg, "time")
            md["date"] = eccodes.codes_get_string(msg, "date")
            md["step"] = eccodes.codes_get_double(msg, "step")

            ldate = eccodes.codes_get_long(msg, "date")
            yyyy = floor(ldate/10000)
            mm = floor((ldate-(yyyy*10000))/100)
            dd = ldate-(yyyy*10000)-mm*100

            forecast_datetime = \
            datetime(yyyy, mm, dd, tzinfo=timezone.utc) \
                + timedelta(minutes=60 * md["time"] / 100) \
                + timedelta(minutes=60 * md["step"])

            md["datetime"] = forecast_datetime

            # decode data
            # get the lats, lons, values
            md["lats"] = eccodes.codes_get_double_array(msg, "latitudes")
            # print(lats)
            md["lons"] = eccodes.codes_get_double_array(msg, "longitudes")
            # print(lons)
            md["values"] = eccodes.codes_get_double_array(msg, "values")
            # print(values)
            eccodes.codes_release(msg)

            messages.append(md)

    f.close()
    return messages

def calc_cossza(message):
    
    lats = message["lats"]
    lons = message["lons"]
    assert lats.size == lons.size

    print(lats.size)

    dt = message["datetime"]
    date = message["date"]
    time = message["time"]
    step = message["step"]

    print(dt.year, dt.month, dt.day, dt.hour)

    # scalar computation
    # cossza = []
    # for i in range(len(lats)):
    #     v = calculate_cos_solar_zenith_angle_integrated(lat=lats[i], lon=lons[i], y=dt.year, m=dt.month, d=dt.day, h=dt.hour, base=time / 100, step=3)
    #     # v = calculate_cos_solar_zenith_angle(lat=lats[i], lon=lons[i], y=dt.year, m=dt.month, d=dt.day, h=dt.hour)
    #     cossza.append(v)

    shape = (message["Nj"], message["Ni"])

    latsmat = np.reshape(lats, shape)
    lonsmat = np.reshape(lons, shape)

    # vectorised computation
    cossza = calculate_cos_solar_zenith_angle(lat=lats, lon=lons, y=dt.year, m=dt.month, d=dt.day, h=dt.hour)
    valsmat = np.reshape(cossza, shape)

    fname = sys.argv[2]
    print('=> ', fname)
    np.savez(fname, lats=latsmat, lons=lonsmat, values=valsmat)
    
    # vectorised computation
    cossza = calculate_cos_solar_zenith_angle_integrated(
        lat=lats, lon=lons, y=dt.year, m=dt.month, d=dt.day, h=dt.hour, base=time/100, step=3)
    valsmat = np.reshape(cossza, shape)

    fname = sys.argv[3]
    print('=> ', fname)
    np.savez(fname, lats=latsmat, lons=lonsmat, values=valsmat)



def main():
    try:
        msgs = decode_grib(sys.argv[1])
        print(msgs)
        for m in msgs:
            calc_cossza(m)

    except eccodes.CodesInternalError as err:
        if eccodes.VERBOSE:
            eccodes.traceback.print_exc(file=sys.stderr)
        else:
            sys.stderr.write(err.msg + '\n')

        return 1


if __name__ == "__main__":
    sys.exit(main())