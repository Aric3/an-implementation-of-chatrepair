import subprocess

def run_command(cmd, encoding='utf-8', cwd=None, timeout=None):
    try:
        finished = subprocess.run(cmd, capture_output=True, cwd=cwd, timeout=timeout)
        finished.check_returncode()
        return True, finished.stdout.decode(encoding), finished.stderr.decode(encoding)
    except subprocess.CalledProcessError:
        return False, finished.stdout.decode(encoding), finished.stderr.decode(encoding)
    except subprocess.TimeoutExpired:
        return False, '{} time out after {} seconds'.format(cmd, timeout), '{} time out after {} seconds'.format(cmd, timeout)

if __name__ == '__main__':
    flag, stdout, stderror = run_command(['defects4j', 'compile'], 'latin-1', 'bugs/Lang11', 5)
    print(stderror)
