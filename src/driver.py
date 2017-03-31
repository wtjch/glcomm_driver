from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadCommandContext, \
    AutoLoadAttribute, AutoLoadResource, AutoLoadDetails
import cas_api.MapsCasApi as MapsCas
import time

SEVERITY_INFO = 20
SEVERITY_ERROR = 40


class QualiError(Exception):
    def __init__(self, name, message):
        self.message = message
        self.name = name

    def __str__(self):
        return  'Cloudshell error at {}. Error is: {}'.format(self.name, self.message)


class GlcommDriver (ResourceDriverInterface):

    def __init__(self):
        pass

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        :param InitCommandContext context: the context the command runs on
        """
        self.ip_maps_server = '192.168.186.141'
        self.tcp_port_maps_server = 10024
        self.cas_client = MapsCas.CasClient(self.ip_maps_server, self.tcp_port_maps_server)
        self.cas_timeout = 20000
        self.line2num = "3035471340"
        self.connected = False
        self.result = 'None'

        self.get_cs_session(server_address=context.connectivity.server_address, res_domain=context.reserveration.domain,
                            admin_token=context.connectivity.admin_auth_token)

        if self.cas_client.connect() == 0:
            self.connected = True
            self.cas_client.start_testbed()
            self.cas_client.load_profile_group()
        else:
            self.api_session.WriteMessageToReservationOutput(self.id, "Connecting to Cas Client Failed")
            self.connected = False


    def _get_cs_session(self, server_address='localhost', res_domain='Global', admin_token=None):
        """
        starts a session to the CloudShell API
        :param str server_address: Address/Hostname of the CloudShell API
        :param str res_domain: Domain for the session to act (based on the reservation's domain)
        :param str admin_token: Admin login token, encrypted
        :return:
        """
        if not self.cs_session or admin_token != self.cs_token:
            self.cs_session = cs_api.CloudShellAPISession(server_address, domain=res_domain, token_id=admin_token)
            self.cs_token = admin_token

    def write_message_to_output(self, message, severity_level=SEVERITY_INFO):
        """
        Write a message to the output window
        :param str message:  The message to be displayed in window
        :param integer severity_level: level of message, if == severity_error, colors red in window
        """
        if severity_level == SEVERITY_INFO:
            self.api_session.WriteMessageToReservationOutput(self.id, message)
        elif severity_level == SEVERITY_ERROR:
            self.api_session.WriteMessageToReservationOutput(self.id, '<font color="red">' + message + '</font>')

    def _report_error(self, error_message, raise_error=True, write_to_output_window=False):
        """
        Report on an error to the log file, output window is optional.There is also an option to raise the error up
        :param str error_message:  The error message you would like to present
        :param bool raise_error:  Do you want to throw an exception
        :param bool write_to_output_window:  Would you like to write the message to the output window
        """
        self.logger.error(error_message)
        if write_to_output_window:
            self.write_message_to_output(error_message, SEVERITY_ERROR)
        if raise_error:
            raise QualiError(self.id, error_message)

    def _report_info(self, message, write_to_output_window=False):
        """
        Report information to the log file, output window is optional.
        :param str message:  The message you would like to present
        :param bool write_to_output_window:  Would you like to write the message to the output window?
        """
        self.logger.info(message)
        if write_to_output_window:
            self.write_message_to_output(message, SEVERITY_INFO)

    def _result_wrapper(self, command, result, line_session, *args):
        if result:
            self.result = 'Pass'
            self._report_info(message='{}:\tSet {} {}'.format(self.result, line_session.port, command),
                             write_to_output_window=True)
        else:
            self.result = 'Fail'
            self._report_error(error_message="{}:\t{} {}".format(self.result, line_session.port, command),
                              raise_error=True,
                              write_to_output_window=True)

    def _open_line(self, maps_session, port):
        opened_line = maps_session.open_line(line=port)
        return dict(line=opened_line, port=port)

    def _go_off_hook(self, line_session):
        try:
            result = line_session.line.offhook()
            self._result_wrapper('OFF HOOK', result, line_session)
        except:
            self._report_error(error_message="{}: Off Hook Exception".format(self.result), raise_error=True, write_to_output_window=True)
            raise

    def _go_on_hook(self, line_session):
        try:
            result = line_session['line'].onhook()
            self._result_wrapper('ON HOOK', result, line_session)
        except:
            self._report_error(error_message="Ofn Hook Exception Error", raise_error=True, write_to_output_window=True)
            raise

    def place_call(self):
        # I'd try to use only the phone numbers - and look up ports as needed, from the devce.
        # in this case, you want to tell this device which number to call from, and what number to call.
        # After that it's just walking through the steps to place a call...
        # build/use methods like self._go_off_hook, self._listen_for_dail_tone, self.dail_digits - etc
        # this way you can trace failure to a specific step with in the process.
        #line_1 = self._open_line(self.cas_client, 37)
        #self._go_off_hook(line_1)
        #
        #self._go_on_hook(line_1)
        line1 = self.cas_client.open_line(line=37)
        print "Onhook"
        print line1.onhook()
        print "Offhook"
        print line1.offhook()
        print "Onhook"
        print line1.onhook()

    # <editor-fold desc="Health Check">

    def health_check(self, cancellation_context):
        """
        Checks if the device is up and connectable
        :return: None
        :exception Exception: Raises an error if cannot connect
        """
        pass

    # </editor-fold>


    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass