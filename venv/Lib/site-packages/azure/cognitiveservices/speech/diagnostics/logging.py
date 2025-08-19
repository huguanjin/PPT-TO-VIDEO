# Copyright (c) Microsoft. All rights reserved.
# See https://aka.ms/csspeech/license for the full license information.
"""
Classes for diagnostics with file-based, memory-based and event-based SDK logging.
"""

import io
import os
import threading
import ctypes
import inspect
from typing import Callable, List

from ..interop import (
    LogLevel, _c_str, _call_hr_fn, _call_long_fn, _call_void_fn, _sdk_lib, _spx_handle, _call_string_function)


class FileLogger:
    """
    A static class to control file-based SDK logging.
    Turning on logging while running your Speech SDK scenario provides
    detailed information from the SDK's core native components. If you
    report an issue to Microsoft, you may be asked to provide logs to help
    Microsoft diagnose the issue. Your application should not take dependency
    on particular log strings, as they may change from one SDK release to another
    without notice.
    FileLogger is the simplest logging solution and suitable for diagnosing
    most on-device issues when running Speech SDK. Added in version 1.43.0

    File logging is a process wide construct. That means that if (for example)
    you have multiple speech recognizer objects running in parallel, there will be one
    log file containing interleaved log lines from all recognizers. You cannot get
    a separate log file for each recognizer.
    """
    def __init__(self):
        raise Exception("cannot instantiate FileLogger directly")

    @staticmethod
    def start(file_path: str, append: bool = False):
        """
        Starts logging to a file. If the file already exists, it will be overwritten unless append is set to True.
        """
        if not file_path or file_path.isspace():
            raise ValueError("The 'file_path' parameter cannot be None or an empty string.")

        directory = os.path.dirname(file_path)
        if directory and not os.path.isdir(directory):
            raise ValueError(f"The directory '{directory}' does not exist.")

        handle = _spx_handle(0)
        _call_hr_fn(fn=_sdk_lib.property_bag_create, *[ctypes.byref(handle)])

        c_file_path = _c_str(file_path)
        c_append = _c_str("1" if append else "0")
        _call_hr_fn(fn=_sdk_lib.property_bag_set_string, *[handle, -1, _c_str("SPEECH-LogFilename"), c_file_path])
        _call_hr_fn(fn=_sdk_lib.property_bag_set_string, *[handle, -1, _c_str("SPEECH-AppendToLogFile"), c_append])
        _call_hr_fn(fn=_sdk_lib.diagnostics_log_start_logging, *[handle, None])

    @staticmethod
    def stop():
        """
        Stops logging to a file.
        This call is optional. If logging has been started,
        the log file will be written when the process exits normally.
        """
        _call_hr_fn(fn=_sdk_lib.diagnostics_log_stop_logging, *[])

    @staticmethod
    def set_filters(filters: List[str] = []):
        """
        Sets filters for logging messages to a file.
        Once filters are set, file logger will only be updated with log strings
        containing at least one of the strings specified by the filters. The match is case sensitive.

        :param filters: Filters to use, or an empty list to remove previously set filters.
        """
        handle = _spx_handle(0)
        _call_hr_fn(fn=_sdk_lib.property_bag_create, *[ctypes.byref(handle)])

        c_filters = _c_str(";".join(filters))
        _call_hr_fn(fn=_sdk_lib.property_bag_set_string, *[handle, -1, _c_str("SPEECH-LogFileFilters"), c_filters])
        _call_hr_fn(fn=_sdk_lib.diagnostics_log_apply_properties, *[handle, None])

    @staticmethod
    def set_level(level: LogLevel = LogLevel.Info):
        """
        Sets the level of the messages to be captured by the logger.

        :param level: Maximum level of detail to be captured by the logger.
        """
        c_logger_type = _c_str("file")
        c_level = _c_str(level.name.lower())
        _call_void_fn(fn=_sdk_lib.diagnostics_set_log_level, *[c_logger_type, c_level])


class MemoryLogger:
    """
    A static class to control SDK logging into an in-memory buffer.
    Turning on logging while running your Speech SDK scenario provides
    detailed information from the SDK's core native components. If you
    report an issue to Microsoft, you may be asked to provide logs to help
    Microsoft diagnose the issue. Your application should not take dependency
    on particular log strings, as they may change from one SDK release to another
    without notice.
    MemoryLogger is designed for the case where you want to get access to logs
    that were taken in the short duration before some unexpected event happens.
    For example, if you are running a Speech Recognizer, you may want to dump the MemoryLogger
    after getting an event indicating recognition was canceled due to some error.
    The size of the memory buffer is fixed at 2MB and cannot be changed. This is
    a "ring" buffer, that is, new log strings written replace the oldest ones
    in the buffer. Added in version 1.43.0

    Memory logging is a process wide construct. That means that if (for example)
    you have multiple speech recognizer objects running in parallel, there will be one
    memory buffer containing interleaved logs from all recognizers. You cannot get
    separate logs for each recognizer.
    """
    def __init__(self):
        raise Exception("cannot instantiate MemoryLogger directly")

    @staticmethod
    def start():
        """
        Starts logging into the internal memory buffer.
        """
        _call_void_fn(fn=_sdk_lib.diagnostics_log_memory_start_logging, *[])

    @staticmethod
    def stop():
        """
        Stops logging into the internal memory buffer.
        """
        _call_void_fn(fn=_sdk_lib.diagnostics_log_memory_stop_logging, *[])

    @staticmethod
    def set_filters(filters: List[str] = []):
        """
        Sets filters for memory logging.
        Once filters are set, memory logger will only be updated with log strings
        containing at least one of the strings specified by the filters. The match is case sensitive.

        :param filters: Filters to use, or an empty list to remove previously set filters.
        """
        c_filters = _c_str(";".join(filters))
        _call_void_fn(fn=_sdk_lib.diagnostics_log_memory_set_filters, *[c_filters])

    @staticmethod
    def set_level(level: LogLevel = LogLevel.Info):
        """
        Sets the level of the messages to be captured by the logger.

        :param level: Maximum level of detail to be captured by the logger.
        """
        c_logger_type = _c_str("memory")
        c_level = _c_str(level.name.lower())
        _call_void_fn(fn=_sdk_lib.diagnostics_set_log_level, *[c_logger_type, c_level])

    @staticmethod
    def dump(file_path: str):
        """
        Writes the content of the whole memory buffer to the specified file.
        It does not block other SDK threads from continuing to log into the buffer.

        :param file_path: Path to a log file on local disk.
        """
        if not file_path or file_path.isspace():
            raise ValueError("The 'file_path' parameter cannot be None or an empty string.")

        directory = os.path.dirname(file_path)
        if directory and not os.path.isdir(directory):
            raise ValueError(f"The directory '{directory}' does not exist.")

        _call_hr_fn(fn=_sdk_lib.diagnostics_log_memory_dump,
                    *[_c_str(file_path), _c_str(""), ctypes.c_bool(False), ctypes.c_bool(False)])

    @staticmethod
    def dump_to_stream(out_stream: io.IOBase):
        """
        Writes the content of the whole memory buffer to an object that implements io.IOBase.
        For example, sys.stdout (for console output).
        It does not block other SDK threads from continuing to log into the buffer.

        :param out_stream: IOBase object to write to.
        """
        if out_stream is None:
            raise ValueError("The 'out_stream' parameter cannot be None.")

        if not isinstance(out_stream, io.IOBase):
            raise ValueError("The 'out_stream' parameter must be an instance of io.IOBase.")

        start = _call_long_fn(fn=_sdk_lib.diagnostics_log_memory_get_line_num_oldest, *[])
        stop = _call_long_fn(fn=_sdk_lib.diagnostics_log_memory_get_line_num_newest, *[])

        if start > stop:
            raise ValueError("The start value cannot be greater than the stop value.")

        for i in range(start, stop):
            line = _call_string_function(fn=_sdk_lib.diagnostics_log_memory_get_line, *[ctypes.c_int(i)])
            if isinstance(out_stream, io.BytesIO):
                out_stream.write(line.encode('utf-8'))
            else:
                out_stream.write(line)

    @staticmethod
    def dump_to_list() -> list:
        """
        Returns the content of the whole memory buffer as a list of strings.
        For example, you can access it as a list by calling MemoryLogger.dump_to_list().
        It does not block other SDK threads from continuing to log into the buffer.

        :return: A list of strings of the contents of the memory buffer copied into it.
        """
        output = []

        start = _call_long_fn(fn=_sdk_lib.diagnostics_log_memory_get_line_num_oldest, *[])
        stop = _call_long_fn(fn=_sdk_lib.diagnostics_log_memory_get_line_num_newest, *[])

        if start > stop:
            raise ValueError("The start value cannot be greater than the stop value.")

        for i in range(start, stop):
            line = _call_string_function(fn=_sdk_lib.diagnostics_log_memory_get_line, *[ctypes.c_int(i)])
            output.append(line)

        return output


class EventLogger:
    """
    A static class to control event-based SDK logging.
    Turning on logging while running your Speech SDK scenario provides
    detailed information from the SDK's core native components. If you
    report an issue to Microsoft, you may be asked to provide logs to help
    Microsoft diagnose the issue. Your application should not take dependency
    on particular log strings, as they may change from one SDK release to another
    without notice.
    Use EventLogger when you want to get access to new log strings as soon
    as they are available, and you need to further process them. For example,
    integrating Speech SDK logs with your existing logging collection system.
    Added in version 1.43.0

    Event logging is a process wide construct. That means that if (for example)
    you have multiple speech recognizer objects running in parallel, you can only register
    one callback function to receive interleaved logs from all recognizers. You cannot register
    a separate callback for each recognizer.
    """
    _lock = threading.Lock()
    _callback = None

    def __init__(self):
        raise Exception("cannot instantiate EventHandler directly")

    @staticmethod
    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def _event_callback(message: bytes):
        """
        Internal callback function to handle event messages.

        :param message: Event message.
        """
        with EventLogger._lock:
            if EventLogger._callback is None:
                raise RuntimeError("EventLogger._callback is None")
            EventLogger._callback(message.decode('utf-8'))

    @staticmethod
    def set_callback(handler: Callable[[str], None] = None):
        """
        Sets event message logging handler.

        :param callback: Event message handler. None to remove the handler from the logger.
        """
        with EventLogger._lock:
            EventLogger._callback = handler
            if handler is None:
                _call_hr_fn(fn=_sdk_lib.diagnostics_logmessage_set_callback, *[None])
            else:
                _call_hr_fn(fn=_sdk_lib.diagnostics_logmessage_set_callback, *[EventLogger._event_callback])

    @staticmethod
    def set_filters(filters: List[str] = []):
        """
        Sets filters for logging event messages.
        Once filters are set, event logger will only be updated with log strings
        containing at least one of the strings specified by the filters. The match is case sensitive.

        :param filters: Filters to use, or an empty list to remove previously set filters.
        """
        c_filters = _c_str(";".join(filters))
        _call_hr_fn(fn=_sdk_lib.diagnostics_logmessage_set_filters, *[c_filters])

    @staticmethod
    def set_level(level: LogLevel = LogLevel.Info):
        """
        Sets the level of the messages to be captured by the logger.

        :param level: Maximum level of detail to be captured by the logger.
        """
        c_logger_type = _c_str("event")
        c_level = _c_str(level.name.lower())
        _call_void_fn(fn=_sdk_lib.diagnostics_set_log_level, *[c_logger_type, c_level])


class SpxTrace:
    """
    Static utility class to log user messages into SDK's internal logging trace.
    Added in version 1.43.0
    """
    def __init__(self):
        raise Exception("cannot instantiate SpxTrace directly")

    @staticmethod
    def _get_caller_info():
        frame = inspect.currentframe().f_back.f_back
        if frame is None:
            return None, None
        file_name = frame.f_code.co_filename
        line_number = frame.f_lineno
        return file_name, line_number

    @staticmethod
    def trace_info(format, args=[], line=None, file=None):
        SpxTrace._trace_helper(LogLevel.Info, "SPX_TRACE_INFO", format, args, line, file)

    @staticmethod
    def trace_warning(format, args=[], line=None, file=None):
        SpxTrace._trace_helper(LogLevel.Warning, "SPX_TRACE_WARNING", format, args, line, file)

    @staticmethod
    def trace_error(format, args=[], line=None, file=None):
        SpxTrace._trace_helper(LogLevel.Error, "SPX_TRACE_ERROR", format, args, line, file)

    @staticmethod
    def trace_verbose(format, args=[], line=None, file=None):
        SpxTrace._trace_helper(LogLevel.Verbose, "SPX_TRACE_VERBOSE", format, args, line, file)

    @staticmethod
    def _trace_helper(level: LogLevel, title, format, args, line, file):
        if line is None or file is None:
            file, line = SpxTrace._get_caller_info()
        if title is None or format is None or args is None or file is None:
            raise ValueError("Arguments cannot be None")
        message = format.format(*args)
        c_level = ctypes.c_int(level.value)
        c_title = _c_str(title)
        c_file = _c_str(file)
        c_line = ctypes.c_int(line)
        c_message = _c_str(message)
        _call_void_fn(fn=_sdk_lib.diagnostics_log_trace_string, *[c_level, c_title, c_file, c_line, c_message])
