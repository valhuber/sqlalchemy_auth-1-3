from sqlalchemy_auth import AuthBase, ALLOW, AuthException
from sqlalchemy_auth.utils import _Settings


class BlockBase(AuthBase):
    """
    _AuthBase provides mechanisms for attribute blocking.

    To block access, return blocked attributes in your own
    _blocked_read_attributes or _blocked_write_attributes.
    """

    def _blocked_read_attributes(self, user):
        """
        Override this method to block read access to attributes, but use
        the get_* methods for access.

        Only called if user != ALLOW.
        """
        return []

    def _blocked_write_attributes(self, user):
        """
        Override this method to block write access to attributes, but use
        the get_* methods for access.

        Only called if user != ALLOW.
        """
        return []

    def get_blocked_read_attributes(self):
        if self._auth_settings.user is not ALLOW:
            return self._blocked_read_attributes(self._auth_settings.user)
        return []

    def get_blocked_write_attributes(self):
        if self._auth_settings.user is not ALLOW:
            return self._blocked_write_attributes(self._auth_settings.user)
        return []

    def get_read_attributes(self):
        attrs = [v for v in vars(self) if not v.startswith("_")]
        return set(attrs) - set(self.get_blocked_read_attributes())

    def get_write_attributes(self):
        attrs = [v for v in vars(self) if not v.startswith("_")]
        return set(attrs) - set(self.get_blocked_write_attributes())

    # make _auth_settings exist at all times.
    #  This matters because sqlalchemy does some magic before __init__ is called.
    # We set it to simplify the logic in __getattribute__
    _auth_settings = _Settings()
    _checking_authorization = False

    def __getattribute__(self, name):
        # __getattribute__ is called before __init__ by a SQLAlchemy decorator.

        # bypass our check if we're recursive
        # this allows _blocked_read_attributes to use self.*
        if super().__getattribute__("_checking_authorization"):
            return super().__getattribute__(name)

        # look up blocked attributes
        super().__setattr__("_checking_authorization", True)
        blocked = self.get_blocked_read_attributes()
        super().__setattr__("_checking_authorization", False)

        # take action
        if name in blocked:
            raise AuthException('{} may not access {} on {}'.format(self._auth_settings.user, name, self.__class__))
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name in self.get_blocked_write_attributes():
            raise AuthException('{} may not access {} on {}'.format(self._auth_settings.user, name, self.__class__))
        return super().__setattr__(name, value)

