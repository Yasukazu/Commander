import os
import contextlib
from contextlib import contextmanager

@contextlib.contextmanager
def pushd(new_dir):
	old_dir = os.getcwd()
	os.chdir(new_dir)
	try:
		yield
	finally:
		os.chdir(old_dir)

if __name__ == '__main__':
    import tempfile
    with tempfile.TemporaryDirectory('_$$$_') as tmpdir:
        absname = ''
        with pushd(tmpdir):
            dirname = '001-dir'
            os.mkdir(dirname)
            with pushd(dirname):
                filename = '001-file'
                with open(filename, 'w') as f:
                    f.write('abc def\n')
                absname = os.path.abspath(filename)
        print(f'file {filename} is created as {absname}')