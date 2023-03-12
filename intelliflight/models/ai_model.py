import intelliflight.util.nws_manager as nws_manager


class AI_Model:
    model_params = None

    def __init__(self, params_path=None):
        """Constructor"""
        if params_path is not None:
            self.load_params(params_path)

    def load_params(self, path: str):
        """Load model parameters"""
        raise NotImplementedError

    def make_prediction(self, src_airport: int, dest_airport: int, operating_airline: str, day_of_week: int, departure_time: str, src_tmp: str, dst_tmp: str, src_wnd: str, dst_wnd: str):
        """Make a prediction based on data.
        Parameters:
        src_airport -- AirportID (from BTS data) of origin airport.
        dest_airport -- AirportID (from BTS data) of destination airport.
        departure_time -- Local time (at src_airport) of departure in format "hhmm"
        """
        raise NotImplementedError
