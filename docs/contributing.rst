.. _contributing:

Contributing
============

There are many ways to contribute to ``speach``.
Currently development team are focusing on:

- Improving :ref:`documentation <contrib_docs>`
- Improving ELAN support
- Fixing bugs :ref:`existing bugs <contrib_bugfix>`

If you have some suggestions or bug reports, please share on `speach issues tracker <https://github.com/neocl/speach/issues>`_.

Code of conduct
---------------

Please read our :ref:`contributor code of conduct <conduct>` for more information.

.. _contrib_bugfix:

Fixing bugs
-----------

If you found a bug please report at https://github.com/neocl/speach/issues

When it is possible, please also share how to reproduce the bugs to help with the bug finding process.

Pull requests are welcome.

.. _contrib_docs:

Updating Documentation
----------------------

1. Fork `speach <https://github.com/neocl/speach>`_ repository to your own Github account.

#. Clone `speach` repository to your local machine.

   .. code:: bash
      
      git clone https://github.com/<your-account-name>/speach
      
#. Create a virtual environment (optional, but highly recommended)

   .. code:: bash

      # if you use virtualenvwrapper
      mkvirtualenv speach
      workon speach

      # if you use Python venv
      python3 -m venv .env
      . .env/bin/activate
      python3 -m pip install --upgrade pip wheel Sphinx

#. Build the docs

   .. code:: bash

      cd docs
      # compile the docs
      make dirhtml
      # serve the docs using Python3 built-in development server
      # Note: this requires Python >= 3.7 to support --directory
      python3 -m http.server 7000 --directory _build/dirhtml

      # if you use earlier Python 3, you may use
      cd _build/dirhtml
      python3 -m http.server 7000

      # if you use Windows, you may use
      python -m http.server 7000 --directory _build/dirhtml

#. Now the docs should be ready to view at http://localhost:7000 . You can visit that URL on your browser to view the docs.

#. More information:

   - Sphinx tutorial: https://sphinx-tutorial.readthedocs.io/start/
   - Using `virtualenv`: https://virtualenvwrapper.readthedocs.io/en/latest/install.html
   - Using `venv`: https://docs.python.org/3/library/venv.html

.. _contrib_dev:

Development
-----------

Development contributions are welcome.
Setting up development environment for speach should be similar to :ref:`contrib_docs`.

Please contact the development team if you need more information: https://github.com/neocl/speach/issues
