Name:             radicale
Version:          0.8
Release:          8%{?dist}
Summary:          A simple CalDAV (calendar) and CardDAV (contact) server
Group:            Applications/Internet
License:          GPLv3+
URL:              http://radicale.org
Source0:          http://pypi.python.org/packages/source/R/Radicale/Radicale-%{version}.tar.gz
Source1:          %{name}-service-unit
Source2:          %{name}-logrotate
Source3:          %{name}-httpd
Source4:          %{name}.te
Source5:          %{name}.fc
Source6:          %{name}.if
# config adjustments for systemwide installation
Patch0:           %{name}-%{version}-systemwide.patch

BuildArch:        noarch
BuildRequires:    python2-devel
BuildRequires:    systemd
Requires(pre):    shadow-utils
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Requires:         python-pam
Requires:         python-ldap

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

%package selinux
Summary:        Selinux policy for Radicale
Requires:       %{name} = %{version}-%{release}
# Hardcode _selinux_policy_version in F20 because of #999584
%if 0%{?fedora} == 20
%global _selinux_policy_version 3.12.1-90
%else
%{!?_selinux_policy_version: %global _selinux_policy_version %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2>/dev/null)}
%endif
%if "%{_selinux_policy_version}" != ""
Requires:      selinux-policy >= %{_selinux_policy_version}
%endif
Requires(post):   /usr/sbin/semodule, /sbin/fixfiles, policycoreutils-python
Requires(postun): /usr/sbin/semodule, /sbin/fixfiles, policycoreutils-python
BuildRequires: checkpolicy, selinux-policy-devel, /usr/share/selinux/devel/policyhelp

%description selinux
Selinux policy for Radicale

%global selinux_types %(%{__awk} '/^#[[:space:]]*SELINUXTYPE=/,/^[^#]/ { if ($3 == "-") printf "%s ", $2 }' /etc/selinux/config 2>/dev/null)
%global selinux_variants %([ -z "%{selinux_types}" ] && echo mls targeted || echo %{selinux_types})

%prep
%setup -q -n Radicale-%{version}
%patch0 -p1
mkdir SELinux
cp -p %{SOURCE4} %{SOURCE5} %{SOURCE6} SELinux

%build
%{__python} setup.py build
cd SELinux
for selinuxvariant in %{selinux_variants}
do
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
    mv %{name}.pp %{name}.pp.${selinuxvariant}
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -

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

install -D -p -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
install -D -p -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
touch %{buildroot}%{_localstatedir}/log/%{name}/%{name}.log

for selinuxvariant in %{selinux_variants}
do
    install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 SELinux/%{name}.pp.${selinuxvariant} \
        %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{name}.pp
done

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
    -c "Radicale service account" %{name}
exit 0

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service 

%post selinux
for selinuxvariant in %{selinux_variants}
do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{name}.pp &> /dev/null || :
done
# http://danwalsh.livejournal.com/10607.html
semanage port -a -t radicale_port_t -p tcp 5232
/sbin/fixfiles -R %{name} restore > /dev/null 2>&1 || :
/sbin/fixfiles -R %{name}-httpd restore > /dev/null 2>&1 || :

%postun selinux
if [ $1 -eq 0 ] ; then
  semanage port -d -p tcp 5232
  for selinuxvariant in %{selinux_variants}
  do
    /usr/sbin/semodule -s ${selinuxvariant} -r %{name} &> /dev/null || :
  done
  /sbin/fixfiles -R %{name} restore > /dev/null 2>&1 || :
  /sbin/fixfiles -R %{name}-httpd restore > /dev/null 2>&1 || :
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
%{_unitdir}/%{name}.service
%dir %attr(750, %{name}, %{name}) %{_localstatedir}/log/%{name}
%ghost %attr(640, %{name}, %{name}) %{_localstatedir}/log/%{name}/%{name}.log
%dir %attr(750, %{name}, %{name}) %{_sharedstatedir}/%{name}/
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/%{name}.wsgi
%{_datadir}/%{name}/%{name}.fcgi

%files httpd
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf

%files selinux
%defattr(-,root,root,0755)
%doc SELinux/*
%{_datadir}/selinux/*/%{name}.pp

%changelog
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
