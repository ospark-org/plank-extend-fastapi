from typing import Optional, Union, List, Tuple, NoReturn

from plank.server.api import BoundedAPI
from plank.server.scheme import SchemeHelper
from plank.service import Service
from plank.utils.path import clearify
from copy import deepcopy

class RoutingSetting:
    @property
    def prefix(self)->Optional[str]:
        return self.__prefix

    @prefix.setter
    def prefix(self, new_value: Optional[str])->NoReturn:
        self.__prefix = new_value

    @property
    def suffix(self)->Optional[str]:
        return self.__suffix

    @suffix.setter
    def suffix(self, new_value: Optional[str])->NoReturn:
        self.__suffix = new_value

    @property
    def path(self)->Optional[str]:
        return self.__path

    def __init__(self, path: Optional[str]=None, prefix: Optional[str]=None, suffix: Optional[str]=None):
        self.__path = path
        self.__prefix = prefix
        self.__suffix = suffix

    def full_path(self)->str:
        paths = []
        if self.__prefix is not None:
            paths.append(clearify(self.__prefix))
        if self.__path is not None:
            paths.append(clearify(self.__path))
        if self.__suffix is not None:
            paths.append(clearify(self.__suffix))
        if len(paths) > 0:
            paths = [""] + paths
        return '/'.join(paths)


class RoutableService(Service):

    __routing_setting__: Optional[RoutingSetting] = None

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.__routing_setting = deepcopy(cls.__routing_setting__)
        return instance

    @property
    def routing(self) -> RoutingSetting:
        if self.__routing_setting is None:
            self.__routing_setting = RoutingSetting()
        return self.__routing_setting

    def get_apis(self, protocol: Optional[Union[str, SchemeHelper]] = None) -> List[Tuple[str, BoundedAPI]]:
        bounded_apis = super().get_apis(protocol=protocol)
        return [
            (
                name,
                api.set_meta_info(key="service_path", value=self.routing.full_path())
                .set_meta_info(key="service_name", value=self.get_name())
            )
            for name, api in bounded_apis
        ]
