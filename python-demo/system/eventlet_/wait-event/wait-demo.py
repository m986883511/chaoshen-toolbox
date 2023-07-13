# from eventlet import event
# import eventlet
#
# evt = event.Event()
#
#
# def waiter():
#     print('about to wait')
#     with eventlet.timeout.Timeout(1):
#         result = evt.wait()
#         print('waited for {0}'.format(result))
#
#
# _ = eventlet.spawn(waiter)
# eventlet.sleep(2)
# # about to wait
# # time.sleep(2)
# evt.send('a')
# eventlet.sleep(0)
#


try:
    import eventlet
    import traceback
    from eventlet import event as event1

    evt = event1.Event()
    print('wait_for_instance_event start')


    def w_waiter():
        print('wait_for_instance_event about to wait')
        with eventlet.timeout.Timeout(1):
            result = evt.wait()
            print('wait_for_instance_event waited for {0}'.format(result))


    eventlet.spawn(w_waiter)
    eventlet.sleep(2)
    evt.send('a')
    eventlet.sleep(0)
except Exception as e:
    err = "wait_for_instance_event error={}, traceback={}".format(str(e), traceback.format_exc())
    print(err)
