import os
import shutil
from subprocess import call
from charms import apt
from charms.reactive import when, when_not, set_state, remove_state, hook
from charmhelpers.core import hookenv, templating, unitdata
from charmhelpers.core.hookenv import status_set, open_port, close_port


config = hookenv.config()
kv = unitdata.kv()


@when('config.changed')
def version_check():
    url = config.get('install_sources')
    key = config.get('install_keys')

    if url != kv.get('nodejs.url') or key != kv.get('nodejs.key'):
        apt.purge(['nodejs'])
        remove_state('nodejs.available')

    if config.changed('port'):
        remove_state('burrow_ui.installed')
        stop_burrowui()
        if config.previous('port'):
            close_port(config.previous('port'))


@when_not('nodejs.available')
def install_nodejs():
    kv.set('nodejs.url', config.get('install_sources'))
    kv.set('nodejs.key', config.get('install_keys'))
    apt.queue_install(['nodejs'])


@when('apt.installed.nodejs')
@when_not('nodejs.available')
def node_js_ready():
    hookenv.status_set('active', 'node.js is ready')
    set_state('nodejs.available')


@when('http.available')
@when_not('burrow_ui.installed')
def install_burrow(http):
    service_host = None
    service_port = None
    services = http.services()
    for service in services:
        service_host = service['hosts'][0]['hostname']
        service_port = service['hosts'][0]['port']
    if not service_host or not service_port:
        return
    if not config.get('port'):
        status_set('blocked', 'Waiting for port config')
        return
    status_set('waiting', 'installing dependencies')
    previous_wd = os.getcwd()
    os.chdir('/home/ubuntu')
    call(['npm', 'install', '-g', '@angular/cli'])
    if os.path.exists('/home/ubuntu/BurrowUI'):
        shutil.rmtree('/home/ubuntu/BurrowUI')
    call(['git', 'clone', 'https://github.com/GeneralMills/BurrowUI.git'])
    os.chdir('/home/ubuntu/BurrowUI')
    call(['npm', 'install'])
    call(['ng', 'build'])
    os.remove('/home/ubuntu/BurrowUI/server/config/server_config.json')
    templating.render(source='server_config.tmpl',
                      target='/home/ubuntu/BurrowUI/server/config/server_config.json',
                      context={
                          'host': service_host + ':' + service_port
                      })
    templating.render(source='unit_file.tmpl',
                      target='/etc/systemd/system/burrowui.service',
                      context={
                          'node_path': '/usr/bin/node',
                          'server_path': '/home/ubuntu/BurrowUI/server.js',
                          'env_vars': ["BURROWUI_PORT=" + str(config.get('port'))]
                      })
    os.chdir(previous_wd)
    set_state('burrow_ui.installed')


@when('burrow_ui.installed')
@when_not('burrow_ui.started')
def start():
    call(['systemctl', 'enable', 'burrowui.service'])
    call(['systemctl', 'start', 'burrowui.service'])
    open_port(config.get('port'))
    status_set('active', 'ready (:' + str(config.get('port')) + ')')
    set_state('burrow_ui.started')


@when('website.available')
def configure_website(website):
    website.configure(port=config.get('port'))


@hook('stop')
def cleanup():
    stop_burrowui()
    if os.path.exists('/home/ubuntu/BurrowUI'):
        shutil.rmtree('/home/ubuntu/BurrowUI')
    if os.path.exists('/etc/systemd/system/burrowui.service'):
        os.remove('/etc/systemd/system/burrowui.service')


def stop_burrowui():
    call(['systemctl', 'stop', 'burrowui'])
    call(['systemctl', 'disable', 'burrowui.service'])
    remove_state('burrow_ui.started')
