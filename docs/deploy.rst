========================
Deploying Your Contracts
========================

::

    brownie deploy [script]

Deployment scripts are stored in the ``deploy`` folder. A deployment script will look something like this:

::

    def deploy():
        kyc = accounts[0].deploy(KYCRegistrar, [accounts[0]], 0)
        issuer = accounts[1].deploy(IssuingEntity, [accounts[1]], 1)
        token = accounts[1].deploy(SecurityToken, issuer, "Test Token", "TST", 1000000)
        issuer.addToken(token)
        issuer.setRegistrar(kyc, True)
