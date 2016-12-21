# test.py
# def application(env, start_reponse):
#     start_reponse('200 OK', [('Content-Type', 'text/html')])
#     return "Hello World"



# test.py
def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"Hello World"] # python3
    #return ["Hello World"] # python2

