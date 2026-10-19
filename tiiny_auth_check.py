"""Read-only connector API probe using the previously supplied local token checker."""
import ast
import contextlib
import io
import ipaddress
import json
import pathlib
import sys
import urllib.error
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def read_token():
    source = pathlib.Path(__file__).with_name('tiiny_token_check.py')
    tree = ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
    main = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main'), None)
    if main is None or not isinstance(main.body[-1], ast.Return):
        raise RuntimeError('Unexpected checker structure')
    last = main.body[-1]
    if not isinstance(last.value, ast.Constant) or last.value.value != 0:
        raise RuntimeError('Unexpected checker success return')
    # Adapt only the in-memory success return; the checker file stays unchanged.
    main.body[-1] = ast.copy_location(ast.Return(value=ast.Name(id='token', ctx=ast.Load())), last)
    ast.fix_missing_locations(tree)
    namespace = {'__name__': 'tiiny_checker_library', '__file__': str(source)}
    old_args = sys.argv
    try:
        sys.argv = [str(source)]
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(tree, str(source), 'exec'), namespace)
            result = namespace['main']()
    finally:
        sys.argv = old_args
    if not isinstance(result, str) or not result.strip():
        raise RuntimeError('Local token check did not succeed')
    return result

def main():
    if len(sys.argv) != 2:
        print('Usage: python tiiny_auth_check.py DEVICE_IPV4')
        return 2
    try:
        host = str(ipaddress.IPv4Address(sys.argv[1]))
    except ValueError:
        print('Invalid IPv4 address.')
        return 2
    try:
        token = read_token()
    except (Exception, SystemExit) as error:
        print('Local checker could not supply a token. Error type:', type(error).__name__)
        print('Keep tiiny_token_check.py beside this script and rerun the original check if needed.')
        return 2
    url = 'http://' + host + '/v1/mcp/servers'
    print('Target:', url)
    print('Method: GET only. No connector or SSH configuration changes.')
    print('Token and response contents will not be displayed or saved.')
    request = urllib.request.Request(url, method='GET', headers={
        'Host': 'connector.api.tiiny',
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/json',
    })
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=20) as response:
            status = response.status
            raw = response.read(4 * 1024 * 1024 + 1)
        print('HTTP status:', status)
        if len(raw) > 4 * 1024 * 1024:
            print('INCONCLUSIVE: response exceeded size limit.')
            return 2
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError):
            print('INCONCLUSIVE: response is not valid JSON. Body hidden.')
            return 2
        if isinstance(data, list):
            print('JSON shape: list; item count:', len(data))
        elif isinstance(data, dict):
            print('JSON shape: object; contents hidden.')
        else:
            print('INCONCLUSIVE: unexpected JSON shape.')
            return 2
        print('RESULT: successful HTTP response from the connector-list endpoint.')
        print('Consistent with accepted authentication; write permissions are not tested.')
        print('Device bootstrap and SSH configuration were not changed.')
        return 0
    except urllib.error.HTTPError as error:
        print('HTTP status:', error.code)
        if error.code in (401, 403):
            print('Authentication or authorization rejected. Do not bootstrap yet.')
        elif 300 <= error.code < 400:
            print('Redirect refused to avoid forwarding credentials elsewhere.')
        else:
            print('Unexpected HTTP error. Response body hidden.')
        return 1
    except Exception as error:
        print('Request failed. Error type:', type(error).__name__)
        print('Details hidden to avoid exposing sensitive data.')
        return 1

if __name__ == '__main__':
    sys.exit(main())
