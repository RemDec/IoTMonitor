import abc
import logging

logging.basicConfig(level=logging.DEBUG)


class Module(abc.ABC):
    """Abstract class used as the base for Module integration framework

    Modules are the provided way to abstract any system program (nmap, snort, ... generally network scanners-like but
    it can be whatever installed on this machine) to integrate it in the application. So that it would be usable and
    manipulable as a standalone unit, its outputs parsable and providing a comprehensible feedback for the others
    application components. The only restriction is that the program must be callable from CLI with a command name
    (nmap for example) and, if output treatment is desired, that those outputs are sent to a standard stream.

    All Modules objects written in order to constitute an overlayer for a real program should implement methods listed
    here. Otherwise, integration in the application environment may lead to errors. Modules classes shouldn't inherit
    this class directly, but one of its children depending on the archetype of program to abstract : ActiveModule and
    PassiveModule.
    """

    def __init__(self):
        self.nbr_modifs = 0
        self.nbr_threats = 0

    def did_modification(self, nbr=1):
        self.nbr_modifs += nbr

    def found_threat(self, nbr=1):
        self.nbr_threats += nbr

    def get_nbr_events(self):
        return self.nbr_modifs, self.nbr_threats

    def treat_params(self, defaults, given_params):
        final_par = {}
        for par, val in defaults.items():
            if given_params.get(par):
                # Parameter is given as is
                final_par[par] = given_params[par]
            elif val[1]:
                # Ungiven parameter but mandatory -> take default
                final_par[par] = val[0]
        return final_par

    @abc.abstractmethod
    def get_description(self):
        """A short description of module activity and purpose of underlying program"""
        pass

    @abc.abstractmethod
    def get_module_id(self):
        """A short string (should be unique among all available modules) used to identify module in the app"""
        pass

    @abc.abstractmethod
    def get_cmd(self):
        """Executable command referring real program underlying module abstraction (nmap, ping, ...)

        It should be a string similar to one used to call the program in CLI
        """
        pass

    @abc.abstractmethod
    def get_params(self):
        """Parameters are used as pairs of keys values to build complete command to call underlying program

        This is the way desirable CLI parameters for the module purpose are managed. In the application, each program
        parameter corresponds to a code and the final called CLI command is built from the cmd and the value of
        parameters accessed by code. Each module should define which parameters it needs and how treat it, ie. which are
        optionals and how to translate it in the CLI command (prefix it with a flag etc.).

        Returns:
            (used, defaults scheme, txt descriptions) a tuple of dictionaries where
                -used is the dict mapping param_code -> value (str) really passed to cmd at exec time
                -defaults dict mapping param_code -> (defaultValue (str), isMandatory (bool), prefix_or_cmd_flag (str))
                -desc provides textual information for each parameter param_code -> description_string
        """
        pass

    @abc.abstractmethod
    def set_params(self, params):
        """Set the current parameters to use at launching time.

        Current parameters value are used in built CLI command if specified. For a mandatory parameter whose code is not
        present in the current paramater dict, the default value defined in default scheme should be used.

        Args:
            params (dict): mapping of some param_code -> given value to use for final command building
        """
        # Dict of params used by the module cmd in CLI at launching (used_param above)
        pass

    @abc.abstractmethod
    def launch(self, rel_to_vi=[]):
        """Method used to start a new execution of underlying program, invoking built command in a parametrized thread.

        The built command should be the same as if call were done directly in CLI considering same program execution
        purpose (same parameters). The command building should be done in this method, as it could also depends on
        the given virtual instances (VI is the in-app virtual representation of a real network device). The program
        execution should occur in a new thread calling distrib_output() on its output when some feedback is available.
        Facilities for this purpose are available in sub-classes, differing in function of program archetype.

        Args:
            rel_to_vi: list of Virtual Instances mapids, used to access VI objects in the Netmap
        """
        pass

    @abc.abstractmethod
    def is_running(self):
        """Retrieve state of threads running underlying program execution if there are some

        Returns:
            running (bool): whether some threads instantiated from Module instance (underlying program execution)
                            are yet running it
        """

    @abc.abstractmethod
    def stop(self):
        """Terminate all running threads linked to this module.

        As underlying programs should be executed in individual threads, control must be kept on those. This method
        should exit all processes in the threads linked with the module instance.
        """
        pass

    @abc.abstractmethod
    def distrib_output(self, output, rel_to_vi=[]):
        """Callback function called on program output

        The output of an underlying program execution has to be parsed in order to translate it in some feedback
        understandable by the application. This job should be done in this method.

        Args:
            output: feedback information (may be error)
            rel_to_vi: VIs the execution was relative to
        """
        pass

    @abc.abstractmethod
    def is_active(self):
        """Getting the archetype of a module

        Returns:
            isactive (bool): whether module is an Active module following archetype definition
        """
        # How a module is classified depending cmd workflow : actives correspond to script execution
        # with unique output at end, passives are processes constantly running in background feeding
        # an output stream with collected information to read and work on
        pass

    @abc.abstractmethod
    def install_info(self):
        """Describe information about the underlying program and how to install it in the system if not yet

        Returns:
             info(dict) : a dictionary structured like that (example for nmap) :
                          {'program': "nmap",
                           'version': "7.2",
                           'install': {
                                       'apt': "nmap",
                                       'yum': "nmap",
                                       'snap': "nmap",
                                       }
                           where program is the command to use in a terminal to call the program (likely in PATH)
                           version is the program version for which the Module has been developed
                           where keys in install are packages managers and values the name of the package in
                           corresponding repositories
                           Every field can be ignored, this method can return an empty dict
        """
        pass
