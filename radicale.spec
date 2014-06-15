Name:             radicale
Version:          0.8
Release:          9%{?dist}
Summary:          A simple CalDAV (calendar) and CardDAV (contact) server
Group:            Applications/Internet
License:          GPLv3+
URL:              http://radicale.org
Source0:          http://pypi.python.org/packages/source/R/Radicale/Radicale-%{version}.tar.gz
Source1:          %{name}.init
Source2:          %{name}-logrotate
Source3:          %{name}-httpd
# config adjustments for systemwide installation
Patch0:           %{name}-%{version}-systemwide.patch
Patch1:           %{name}-%{version}-pidfile.patch

BuildArch:        noarch
BuildRequires:    python2-devel
Requires(pre):    shadow-utils
Requires:         python-pam
Requires:         python-ldap

#Initscripts
Requires(post): chkconfig
Requires(preun): chkconfig initscripts

%description
The Radicale Project is a CalDAV (calendar) and CardDAV (contact) server. It
aims to be a light solution, easy to use, easy to install, easy to configure.
As a consequence, it requires few software dependencies and is pre-configured
to work out-of-the-box.

The Radicale Project runs on most of the UNIX-like platforms (Linux, BSD,
MacOS X) and Windows. It is known to work with Evolution, Lightning, iPhone
and Android clients. It is free and open-source software, released under GPL
version 3.

For further information, please visit the Radicale Website
http://www.radicale.org

%package httpd
Summary:        httpd config for Radicale
Requires:       %{name} = %{version}-%{release}
Requires:       httpd
Requires:       mod_wsgi

%description httpd
httpd config for Radicale

%prep
%setup -q -n Radicale-%{version}
%patch0 -p1
%patch1 -p1

%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root %{buildroot}

# Install configuration files
mkdir -p %{buildroot}%{_sysconfdir}/%{name}/
install -p -m 640 config %{buildroot}%{_sysconfdir}/%{name}/
install -p -m 644 logging %{buildroot}%{_sysconfdir}/%{name}/

# Install wsgi file
mkdir -p %{buildroot}%{_datadir}/%{name}
install -p -m 755 radicale.wsgi %{buildroot}%{_datadir}/%{name}/
install -p -m 755 radicale.fcgi %{buildroot}%{_datadir}/%{name}/

# Install apache's configuration file
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d/
install -p -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/httpd/conf.d/%{name}.conf

# Create folder where the calendar will be stored
mkdir -p  %{buildroot}%{_sharedstatedir}/%{name}/

install -D -p -m 644 %{SOURCE1} %{buildroot}%{_initrddir}/%{name}
install -D -p -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}
touch %{buildroot}%{_localstatedir}/log/%{name}/%{name}.log

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
    -c "Radicale service account" %{name}
exit 0

%post
if [ $1 -eq 1 ]; then
    /sbin/chkconfig --add %{name}
fi

%preun
if [ $1 = 0 ] ; then
    /sbin/service radicale stop >/dev/null 2>&1
    /sbin/chkconfig --del radicale
fi

%files
%doc COPYING README NEWS.rst TODO.rst
%dir %attr(0755, %{name}, %{name}) %{_sysconfdir}/%{name}/
%config(noreplace) %attr(0640, %{name}, %{name}) %{_sysconfdir}/%{name}/config
%config(noreplace) %attr(0644, %{name}, %{name}) %{_sysconfdir}/%{name}/logging
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{python_sitelib}/%{name}
%{python_sitelib}/Radicale-*.egg-info
%{_bindir}/%{name}
%dir %attr(700, %{name}, %{name}) %{_localstatedir}/run/%{name}
%attr(755, root, root) %{_initrddir}/%{name}
%dir %attr(750, %{name}, %{name}) %{_localstatedir}/log/%{name}
%ghost %attr(640, %{name}, %{name}) %{_localstatedir}/log/%{name}/%{name}.log
%dir %attr(750, %{name}, %{name}) %{_sharedstatedir}/%{name}/
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/%{name}.wsgi
%{_datadir}/%{name}/%{name}.fcgi

%files httpd
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf

%changelog
* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue Apr 29 2014 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.8-8
- Add PrivateDevices to unit file

* Wed Dec 25 2013 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.8-7
- SELinux policy 1.0.2

* Fri Nov 29 2013 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.8-6
- SELinux policy 1.0.1 fix bug #1035925

* Fri Nov 08 2013 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.8-5
- Hardcode _selinux_policy_version in F20 because of #999584

* Thu Oct 03 2013 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.8-4
- Update httpd config file and add SELinux policy. Bug #1014408

* Tue Aug 27 2013 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.8-3
- Move .wsgi and .fcgi to main package

* Sun Jul 21 2013 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.8-2
- BuildRequire python2-devel

* Thu Jul 18 2013 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.8-1
- Update to version 0.8
- Merge Till Maas's spec file. Bug #922276

* Mon Jul 08 2013 Juan Orti Alcaine <jorti@fedoraproject.org> - 0.7.1-1
- Initial packaging
