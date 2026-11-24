# SRML Mobile external sample add-on

This is a separate DLL implementing `ISrmlMobilePlugin` from `SRMLMobile.API`.

The Runtime Adapter discovers this exact sample assembly in its dedicated add-on test folder and invokes its public parameterless entry point. The plugin only writes log messages and does not access Unity/game objects.

It is a proof of the external assembly boundary, not yet the general-purpose add-on manager or a security sandbox.
