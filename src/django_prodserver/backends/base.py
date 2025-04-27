class BaseServerBackend:
    def __init__(self, **server_args):
        self.args = self._format_server_args_from_dict(server_args.get("ARGS"))

    def start_server(self, *args):
        raise NotImplementedError

    def prep_server_args(self):
        return self.args

    def _format_server_args_from_dict(self, args):
        """
        This function transforms the dictionary settings configuration
        from:
            {
                "bind": "0.0.0.0:8111"
            }
        to
            [
                "--bind=0.0.0.0:8111"
            ]
        """
        return [f"--{arg_name}={arg_value}" for arg_name, arg_value in args.items()]

    # def run_from_argv(self, argv):
    # TODO: The below should be looked into and implemented
    #     if getattr(settings, "WEBSERVER_WARMUP", True):
    #         app = get_internal_wsgi_application()
    #         if getattr(settings, "WEBSERVER_WARMUP_HEALTHCHECK", None):
    #             wsgi_healthcheck(app, settings.WEBSERVER_WARMUP_HEALTHCHECK)
    #     # self.start_server(*self.prep_server_args())
