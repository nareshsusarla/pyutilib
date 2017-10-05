import os
import sys
import glob
import optparse

import pyutilib.subprocess
from pyutilib.th import TestCase

from os.path import dirname

if sys.platform.startswith('win'):
    platform = 'win'
    use_exec = True
else:
    platform = 'linux'
    use_exec = True


def run(package, basedir, argv, use_exec=use_exec, env=None):
    if type(package) not in (list, tuple):
        package = [package]

    parser = optparse.OptionParser(usage='run [OPTIONS] <dirs>')

    parser.add_option(
        '-v',
        '--verbose',
        action='store_true',
        dest='verbose',
        default=False,
        help='Verbose output')
    parser.add_option(
        '--cat',
        '--category',
        action='append',
        dest='cat',
        default=[],
        help='Specify the test category.')
    parser.add_option(
        '--cov',
        '--coverage',
        action='store_true',
        dest='coverage',
        default=False,
        help='Enable the computation of coverage information')
    parser.add_option(
        '-d',
        '--dir',
        action='store',
        dest='dir',
        default=None,
        help='Top-level source directory where the tests are applied.')
    parser.add_option(
        '-p',
        '--package',
        action='store',
        dest='pkg',
        default=package[0],
        help='Limit the coverage to this package')
    parser.add_option(
        '-o',
        '--output',
        action='store',
        dest='output',
        default=None,
        help='Redirect output to a file')
    parser.add_option('--with-doctest',
        action='store_true',
        dest='doctests',
        default=False,
        help='Run tests included in Sphinx documentation')
    parser.add_option('--doc-dir',
        action='store',
        dest='docdir',
        default=None,
        help='Top-level source directory for Sphinx documentation')
    parser.add_option('--no-xunit',
        action='store_false',
        dest='xunit',
        default=True,
        help='Disable the nose XUnit plugin')
    parser.add_option('--dry-run',
        action='store_true',
        dest='dryrun',
        default=False,
        help='Dry run: collect but do not execute the tests')

    options, args = parser.parse_args(argv)

    if env is None:
        env = os.environ.copy()

    if options.output:
        options.output = os.path.abspath(options.output)

    if options.dir is None:
        os.chdir(basedir)
    else:
        os.chdir(options.dir)

    CWD = os.getcwd()
    print("Running tests in directory %s" % (CWD,))

    if platform == 'win':
        binDir = os.path.join(sys.exec_prefix, 'Scripts')
        nosetests = os.path.join(binDir, 'nosetests.exe')
        #
        # JDS [2 Oct 2017]: I am not sure why this was here.  If we find
        # we need it, we can re-add it with an explanation as to why
        # Windows needs special PYTHONPATH handling.
        #
        #srcdirs = []
        #for dir in glob.glob('*'):
        #    if os.path.isdir(dir):
        #        srcdirs.append(os.path.abspath(dir))
        #if 'PYTHONPATH' in env:
        #    srcdirs.append(env['PYTHONPATH'])
        #env['PYTHONPATH'] = os.pathsep.join(srcdirs)
    else:
        binDir = os.path.join(sys.exec_prefix, 'bin')
        nosetests = os.path.join(binDir, 'nosetests')

    if os.path.exists(nosetests):
        cmd = [nosetests]
    else:
        cmd = ['nosetests']

    if binDir not in env['PATH']:
        env['PATH'] = os.pathsep.join([binDir, env.get('PATH','')])

    if options.coverage:
        cmd.extend(['--with-coverage', '--cover-erase'])
        if options.pkg:
            cmd.append('--cover-package=%s' % options.pkg)
        env['COVERAGE_FILE'] = os.path.join(CWD, '.coverage')

    if options.verbose:
        cmd.append('-v')
    if options.dryrun:
        cmd.append('--collect-only')

    if options.doctests:
        cmd.extend(['--with-doctest', '--doctest-extension=.rst'])
        if options.docdir:
            docdir = os.path.abspath(_options.docdir)
            if not os.path.exists(docdir):
                raise ValueError("Invalid documentation directory, "
                                 "path does not exist")

    if options.xunit:
        cmd.append('--with-xunit')
        cmd.append('--xunit-file=TEST-' + package[0] + '.xml')

    attr = []
    _with_performance = False
    if 'PYUTILIB_UNITTEST_CATEGORY' in env:
        _categories = TestCase.parse_categories(
            env.get('PYUTILIB_UNITTEST_CATEGORY', '') )
    else:
        _categories = []
        for x in options.cat:
            _categories.extend( TestCase.parse_categories(x) )
        if not _categories:
            _categories.extend( TestCase.parse_categories('smoke') )

    # If no one specified a category, default to "smoke"
    if not _categories:
        _categories = [ (('smoke',1),) ]
    # process each category set (that is, each conjunction of categories)
    for _category_set in _categories:
        _attrs = []
        # "ALL" deletes the categories, and just runs everything.  Note
        # that "ALL" disables performance testing
        if ('all', 1) in _category_set:
            _categories = []
            _with_performance = False
            attr = []
            break
        # For each category set, unless the user explicitly says
        # something about fragile, assume that fragile should be
        # EXCLUDED.
        if ('fragile',1) not in _category_set \
           and ('fragile',0) not in _category_set:
            _category_set = _category_set + (('fragile',0),)
        # Process each category in the conjection and add to the nose
        # "attrib" plugin arguments
        for _category, _value in _category_set:
            if not _category:
                continue
            _attrs.append("%s=%s" % (_category, _value))
            if _category == 'performance' and _value == 1:
                _with_performance = True
        if _attrs:
            attr.append('-a')
            attr.append(','.join(_attrs))
    cmd.extend(attr)
    if attr:
        print(" ... for test categor%s: %s" %
              ('y' if len(attr)<=2 else 'ies',
               ' '.join(attr[1::2])))

    if _with_performance:
        cmd.append('--with-testdata')
        env['NOSE_WITH_TESTDATA'] = '1'
        env['NOSE_WITH_FORCED_GC'] = '1'

    targets = set()
    if len(args) <= 1:
        targets.update(package)
    else:
        for arg in args[1:]:
            if '*' in arg or '?' in arg:
                targets.update(glob.glob(arg))
            else:
                targets.add(arg)
    cmd.extend(list(targets))

    print("Running...\n    %s\n" % (' '.join(cmd),))
    rc = 0
    if sys.platform.startswith('java'):
        import subprocess
        p = subprocess.Popen(cmd, env=env)
        p.wait()
        rc = p.returncode
    elif options.output:
        sys.stdout.write("Redirecting output to file '%s' ..." % options.output)
        rc, _ = pyutilib.subprocess.run(cmd, env=env, outfile=options.output)
    elif use_exec:
        rc = None
        os.execvpe(cmd[0], cmd, env)
    else:
        sys.stdout.flush()
        rc, _ = pyutilib.subprocess.run(cmd, env=env, ostream=sys.stdout)
        sys.stdout.flush()
    return rc


def runPyUtilibTests(argv=None, use_exec=use_exec):
    if argv is None:
        argv = sys.argv

    return pyutilib.dev.runtests.run(
        'pyutilib',
        dirname(dirname(dirname(os.path.abspath(__file__)))),
        argv,
        use_exec=use_exec )
