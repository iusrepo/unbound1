%{?!with_python:      %global with_python      1}

%if %{with_python}
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}
%endif

%if 0%{?rhel}
%{!?munin:%define munin 0}
%else
%{!?munin:%define munin 1}
%endif

Summary: Validating, recursive, and caching DNS(SEC) resolver
Name: unbound
Version: 1.4.19
Release: 5%{?dist}
License: BSD
Url: http://www.nlnetlabs.nl/unbound/
Source: http://www.unbound.net/downloads/%{name}-%{version}.tar.gz
Source1: unbound.service
Source2: unbound.conf
Source3: unbound.munin
Source4: unbound_munin_
Source5: root.key
Source6: dlv.isc.org.key
Source7: unbound-keygen.service
Source8: tmpfiles-unbound.conf
Source9: example.com.key
Source10: example.com.conf
Source11: block-example.com.conf
# From http://data.iana.org/root-anchors/icannbundle.pem
Source12: icannbundle.pem
Source13: root.anchor
Source14: unbound.sysconfig
Source15: unbound-monthly.cron
Source16: unbound-munin.README
Patch1: unbound-1.4.19-888759.patch
Group: System Environment/Daemons
BuildRequires: flex, openssl-devel , ldns-devel >= 1.6.13
BuildRequires: libevent-devel expat-devel
%if %{with_python}
BuildRequires:  python-devel swig
%endif
BuildRequires: systemd-units
# Required for SVN versions
# BuildRequires: bison

Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Requires: ldns >= 1.6.13
Requires(pre): shadow-utils
# Needed because /usr/sbin/unbound links unbound libs staticly
Requires: %{name}-libs%{?_isa} = %{version}-%{release}

Obsoletes:      dnssec-conf < 1.27-2
Provides:       dnssec-conf = 1.27-1

%description
Unbound is a validating, recursive, and caching DNS(SEC) resolver.

The C implementation of Unbound is developed and maintained by NLnet
Labs. It is based on ideas and algorithms taken from a java prototype
developed by Verisign labs, Nominet, Kirei and ep.net.

Unbound is designed as a set of modular components, so that also
DNSSEC (secure DNS) validation and stub-resolvers (that do not run
as a server, but are linked into an application) are easily possible.

%if %{munin}
%package munin
Summary: Plugin for the munin / munin-node monitoring package
Group:     System Environment/Daemons
Requires: munin-node
Requires: %{name} = %{version}-%{release}, bc
BuildArch: noarch

%description munin
Plugin for the munin / munin-node monitoring package
%endif

%package devel
Summary: Development package that includes the unbound header files
Group: Development/Libraries
Requires: %{name}-libs%{?_isa} = %{version}-%{release}, openssl-devel, ldns-devel

%description devel
The devel package contains the unbound library and the include files

%package libs
Summary: Libraries used by the unbound server and client applications
Group: Applications/System
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig
Requires: openssl >= 0.9.8g-12

%description libs
Contains libraries used by the unbound server and client applications

%if %{with_python}
%package python
Summary: Python modules and extensions for unbound
Group: Applications/System
Requires: %{name}-libs%{?_isa} = %{version}-%{release}

%description python
Python modules and extensions for unbound
%endif

%prep
%setup -q 
%patch1 -p1 -b .888759

%build
export LDFLAGS="$LDFLAGS -Wl,-z,now"
%configure  --with-ldns= --with-libevent --with-pthreads --with-ssl \
            --disable-rpath --disable-static \
            --with-conf-file=%{_sysconfdir}/%{name}/unbound.conf \
            --with-pidfile=%{_localstatedir}/run/%{name}/%{name}.pid \
%if %{with_python}
            --with-pythonmodule --with-pyunbound \
%endif
            --enable-sha2 --disable-gost --disable-ecdsa

%{__make} %{?_smp_mflags}
%{__make} %{?_smp_mflags} streamtcp

%install
%{__make} DESTDIR=%{buildroot} install
install -d 0755 %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
install -p -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/unbound.service
install -p -m 0644 %{SOURCE7} %{buildroot}%{_unitdir}/unbound-keygen.service
install -p -m 0755 %{SOURCE2} %{buildroot}%{_sysconfdir}/unbound
install -p -m 0644 %{SOURCE12} %{buildroot}%{_sysconfdir}/unbound
install -p -m 0644 %{SOURCE14}  %{buildroot}%{_sysconfdir}/sysconfig/unbound
install -p -m 0644 %{SOURCE16}  .
install -d 0755 %{buildroot}%{_sysconfdir}/cron.monthly
install -p -m 0755 %{SOURCE15}   %{buildroot}%{_sysconfdir}/cron.monthly/unbound-anchor
%if %{munin}
# Install munin plugin and its softlinks
install -d 0755 %{buildroot}%{_sysconfdir}/munin/plugin-conf.d
install -p -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/munin/plugin-conf.d/unbound
install -d 0755 %{buildroot}%{_datadir}/munin/plugins/
install -p -m 0755 %{SOURCE4} %{buildroot}%{_datadir}/munin/plugins/unbound
for plugin in unbound_munin_hits unbound_munin_queue unbound_munin_memory unbound_munin_by_type unbound_munin_by_class unbound_munin_by_opcode unbound_munin_by_rcode unbound_munin_by_flags unbound_munin_histogram; do
    ln -s unbound %{buildroot}%{_datadir}/munin/plugins/$plugin
done
%endif

# install streamtcp used for monitoring / debugging unbound's port 80/443 modes
install -m 0755 streamtcp %{buildroot}%{_sbindir}/unbound-streamtcp

# Install tmpfiles.d config
mkdir -p %{buildroot}%{_sysconfdir}/tmpfiles.d/
install -m 0644 %{SOURCE8} %{buildroot}%{_sysconfdir}/tmpfiles.d/unbound.conf

# install root and DLV key
install -m 0644 %{SOURCE5} %{SOURCE6} %{SOURCE13} %{buildroot}%{_sysconfdir}/unbound/

# remove static library from install (fedora packaging guidelines)
rm %{buildroot}%{_libdir}/*.la
%if %{with_python}
rm %{buildroot}%{python_sitearch}/*.la
%endif

# create softlink for all functions of libunbound man pages
for mpage in ub_ctx ub_result ub_ctx_create ub_ctx_delete ub_ctx_set_option ub_ctx_get_option ub_ctx_config ub_ctx_set_fwd ub_ctx_resolvconf ub_ctx_hosts ub_ctx_add_ta ub_ctx_add_ta_file ub_ctx_trustedkeys ub_ctx_debugout ub_ctx_debuglevel ub_ctx_async ub_poll ub_wait ub_fd ub_process ub_resolve ub_resolve_async ub_cancel ub_resolve_free ub_strerror ub_ctx_print_local_zones ub_ctx_zone_add ub_ctx_zone_remove ub_ctx_data_add ub_ctx_data_remove;
do
  echo ".so man3/libunbound.3" > %{buildroot}%{_mandir}/man3/$mpage ;
done

mkdir -p %{buildroot}%{_localstatedir}/run/unbound

# Install directories for easier config file drop in

mkdir -p %{buildroot}%{_sysconfdir}/unbound/{keys.d,conf.d,local.d}
install -p %{SOURCE9} %{buildroot}%{_sysconfdir}/unbound/keys.d/
install -p %{SOURCE10} %{buildroot}%{_sysconfdir}/unbound/conf.d/
install -p %{SOURCE11} %{buildroot}%{_sysconfdir}/unbound/local.d/

# Symlink unbound-control-setup.8 manpage to unbound-control.8
ln -s %{_mandir}/man8/unbound-control.8 %{buildroot}/%{_mandir}/man8/unbound-control-setup.8

%files 
%doc doc/README doc/CREDITS doc/LICENSE doc/FEATURES
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}-keygen.service
%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%attr(0755,unbound,unbound) %dir %{_localstatedir}/run/%{name}
%config(noreplace) %{_sysconfdir}/tmpfiles.d/unbound.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/unbound.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%attr(0775,root,unbound) %config(noreplace) %{_sysconfdir}/%{name}/keys.d
%attr(0775,root,unbound) %config(noreplace) %{_sysconfdir}/%{name}/conf.d
%attr(0775,root,unbound) %config(noreplace) %{_sysconfdir}/%{name}/local.d
%{_sbindir}/unbound
%{_sbindir}/unbound-checkconf
%{_sbindir}/unbound-control
%{_sbindir}/unbound-control-setup
%{_sbindir}/unbound-host
%{_sbindir}/unbound-streamtcp
%{_mandir}/man1/*
%{_mandir}/man5/*
%{_mandir}/man8/*

%if %{with_python}
%files python
%{python_sitearch}/*
%doc libunbound/python/examples/*
%doc pythonmod/examples/*
%endif

%if %{munin}
%files munin
%config(noreplace) %{_sysconfdir}/munin/plugin-conf.d/unbound
%{_datadir}/munin/plugins/unbound*
%doc unbound-munin.README
%endif

%files devel
%{_libdir}/libunbound.so
%{_includedir}/unbound.h
%{_mandir}/man3/*
%doc README

%files libs
%{_sbindir}/unbound-anchor
%{_libdir}/libunbound.so.*
%{_sysconfdir}/%{name}/icannbundle.pem
%{_sysconfdir}/cron.monthly/unbound-anchor
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/root.anchor
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/root.key
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/dlv.isc.org.key
%doc doc/README doc/LICENSE

%pre
getent group unbound >/dev/null || groupadd -r unbound
getent passwd unbound >/dev/null || \
useradd -r -g unbound -d %{_sysconfdir}/unbound -s /sbin/nologin \
-c "Unbound DNS resolver" unbound
exit 0

%post
%systemd_post unbound.service
%systemd_post unbound-keygen.service
%systemd_post unbound-rootkey.service

%post libs 
/sbin/ldconfig
%{_sysconfdir}/cron.monthly/unbound-anchor

%preun
%systemd_preun unbound.service
%systemd_preun unbound-keygen.service
%systemd_preun unbound-rootkey.service

%postun 
%systemd_postun_with_restart unbound.service
%systemd_postun unbound-keygen.service
%systemd_postun unbound-rootkey.service

%postun libs -p /sbin/ldconfig

%triggerun -- unbound < 1.4.12-4
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply unbound
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save unbound >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del unbound >/dev/null 2>&1 || :
/bin/systemctl try-restart unbound.service >/dev/null 2>&1 || :
/bin/systemctl try-restart unbound-keygen.service >/dev/null 2>&1 || :

%changelog
* Tue Mar 05 2013 Adam Tkac <atkac redhat com> - 1.4.19-5
- build with full RELRO
- symlink unbound-control-setup.8 manpage to unbound-control.8

* Fri Feb 15 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.19-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Dec 12 2012 Paul Wouters <pwouters@redhat.com> - 1.4.19-3
- Updated to 1.4.19 - this integrates all existing patches
- Patch for unbound-anchor (rhbz#888759)

* Fri Nov 09 2012 Paul Wouters <pwouters@redhat.com> - 1.4.18-6
- Patch to ensure stube-zone's aren't lost when using dnssec-triggerd
- added unbound-munin.README file

* Wed Sep 26 2012 Paul Wouters <pwouters@redhat.com> - 1.4.18-5
- Patch to allow wildcards in include: statements
- Add directories /etc/unbound/keys.d,conf.d,local.d with
  example entries
- Added /etc/unbound/root.anchor, maintained by unbound-anchor
  which is installed as monthly cron and PreExec in systemd config
  (root.key is unused, but left installed in case people depend on it)
- Native systemd (simple) and /etc/sysconfig/unbound support
- Run unbound-checkconf in PreExec
- Moved trust anchor related files to unbound-libs, as they can
  be used without the daemon.
- sub packages now depends on base package of same arch
- Build munin package as noarch
- unbound-anchor moved to unbound-libs package. It is needed
  to update the root.anchor key file.

* Tue Sep 04 2012 Paul Wouters <pwouters@redhat.com> - 1.4.18-3
- Fix openssl thread locking bug under high query load

* Thu Aug 23 2012 Paul Wouters <pwouters@redhat.com> - 1.4.18-2
- Use new systemd-rpm macros (rhbz#850351)
- Clean up old obsoleted dnssec-conf from < fedora 15

* Fri Aug 03 2012 Paul Wouters <pwouters@redhat.com> - 1.4.18-1
- Updated to 1.4.18 (FIPS related fixes mostly)
- Removed patches that were merged in upstream
- Added comment to root.key

* Mon Jul 23 2012 Paul Wouters <pwouters@redhat.com> - 1.4.17-5
- Fix for unbound crasher (upstream bug #452)
- Support libunbound functions in man pages and place in -devel

* Sun Jul 22 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.17-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jul 03 2012 Paul Wouters <pwouters@redhat.com> - 1.4.17-3
- unbound FIPS patches for MD5,randomness (rhbz#835106)

* Fri Jun 15 2012 Adam Tkac <atkac redhat com> - 1.4.17-2
- don't build unbound-munin on RHEL

* Thu May 24 2012 Paul Wouters <pwouters@redhat.com> - 1.4.17-1
- Updated to 1.4.17 (which mostly brings in patches we already
  applied from svn trunk)

* Wed Feb 29 2012 Paul Wouters <pwouters@redhat.com> - 1.4.16-3 
- Since the daemon links to the libs staticly, add Requires:
  (this is rhbz#745288)
- Package up streamtcp as unbound-streamtcp (for monitoring)

* Mon Feb 27 2012 Paul Wouters <pwouters@redhat.com> - 1.4.16-2
- Don't ghost the directory (rhbz#788805)
- Patch for unbound to support unbound-control forward_zone
  (needed for openswan in XAUTH mode)

* Thu Feb 02 2012 Paul Wouters <paul@nohats.ca> - 1.4.16-1
- Upgraded to 1.4.16, which was relesed due to the soname
  and some DNSSEC validation failures

* Wed Feb 01 2012 Paul Wouters <paul@nohats.ca> - 1.4.15-2
- Patch for SONAME version (libtool's -version-number vs -version-info)

* Fri Jan 27 2012 Paul Wouters <pwouters@redhat.com> - 1.4.15-1
- Upgraded to 1.4.15
- Updated unbound.conf to show how to configure listening on tls443

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.14-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Dec 19 2011 Paul Wouters <paul@cypherpunks.ca> - 1.4.14-1
- Upgraded to 1.4.14 for CVE-2011-4528 / VU#209659
- SSL-wrapped query support for dnssec-trigger
- EDNS handling changes
- Removed integrated EDNS patches
- Disabled use-caps-for-id, GoDaddy domains now break on it
- Enabled new harden-below-nxdomain

* Thu Sep 15 2011 Paul Wouters <paul@xelerance.com> - 1.4.13-1
- Upgraded to 1.4.13
- Removed merged in pythonmod patch
- Added EDNS1480 patch to fix unbound on broken EDNS/UDP networks
- Fix python to go into sitearch instead of sitelib

* Wed Sep 14 2011 Tom Callaway <spot@fedoraproject.org> - 1.4.12-4
- convert to systemd, tmpfiles.d

* Mon Aug 08 2011 Paul Wouters <paul@xelerance.com> - 1.4.12-3
- Added pythonmod docs and examples

* Mon Aug 08 2011 Paul Wouters <paul@xelerance.com> - 1.4.12-2
- Fix for python module load in the server (Tom Hendrikx)
- No longer enable --enable-debug as it causes degraded  performance
  under load.

* Mon Jul 18 2011 Paul Wouters <paul@xelerance.com> - 1.4.12-1
- Updated to 1.4.12

* Sun Jul 03 2011 Paul Wouters <paul@xelerance.com> - 1.4.11-1
- Updated to 1.4.11
- removed integrated CVE patch
- updated stock unbound.conf for new options introduced

* Mon Jun 06 2011 Paul Wouters <paul@xelerance.com> - 1.4.10-1
- Added ghost for /var/run/unbound (bz#656710)

* Mon Jun 06 2011 Paul Wouters <paul@xelerance.com> - 1.4.9-3
- rebuilt

* Wed May 25 2011 Paul Wouters <paul@xelerance.com> - 1.4.9-2
- Applied patch for CVE-2011-1922 DoS vulnerability

* Sun Mar 27 2011 Paul Wouters <paul@xelerance.com> - 1.4.9-1
- Updated to 1.4.9

* Sat Feb 12 2011 Paul Wouters <paul@xelerance.com> - 1.4.8-2
- rebuilt

* Tue Jan 25 2011 Paul Wouters <paul@xelerance.com> - 1.4.8-1
- Updated to 1.4.8
- Enable root key for DNSSEC
- Fix unbound-munin to use proper file (could cause excessive logging)
- Build unbound-python per default
- Disable gost as Fedora/EPEL does not allow ECC and has mangled openssl

* Tue Oct 26 2010 Paul Wouters <paul@xelerance.com> - 1.4.5-4
- Revert last build - it was on the wrong branch

* Tue Oct 26 2010 Paul Wouters <paul@xelerance.com> - 1.4.5-3
- Disable do-ipv6 per default - causes severe degradation on non-ipv6 machines
  (see comments in inbound.conf)

* Tue Jun 15 2010 Paul Wouters <paul@xelerance.com> - 1.4.5-2
- Bump release - forgot to upload the new tar ball.

* Tue Jun 15 2010 Paul Wouters <paul@xelerance.com> - 1.4.5-1
- Upgraded to 1.4.5

* Mon May 31 2010 Paul Wouters <paul@xelerance.com> - 1.4.4-2
- Added accidentally omitted svn patches to cvs 

* Mon May 31 2010 Paul Wouters <paul@xelerance.com> - 1.4.4-1
- Upgraded to 1.4.4 with svn patches
- Obsolete dnssec-conf to ensure it is de-installed

* Thu Mar 11 2010 Paul Wouters <paul@xelerance.com> - 1.4.3-1
- Update to 1.4.3 that fixes 64bit crasher

* Tue Mar 09 2010 Paul Wouters <paul@xelerance.com> - 1.4.2-1
- Updated to 1.4.2 
- Updated unbound.conf with new options
- Enabled pre-fetching DNSKEY records (DNSSEC speedup)
- Enabled re-fetching popular records before they expire
- Enabled logging of DNSSEC validation errors

* Mon Mar 01 2010 Paul Wouters <paul@xelerance.com> - 1.4.1-5
- Overriding -D_GNU_SOURCE is no longer needed. This fixes DSO issues
  with pthreads

* Wed Feb 24 2010 Paul Wouters <paul@xelerance.com> - 1.4.1-3
- Change make/configure lines to attempt to fix -lphtread linking issue

* Thu Feb 18 2010 Paul Wouters <paul@xelerance.com> - 1.4.1-2
- Removed dependancy for dnssec-conf
- Added ISC DLV key (formerly in dnssec-conf)
- Fixup old DLV locations in unbound.conf file via %%post
- Fix parent child disagreement handling and no-ipv6 present [svn r1953]

* Tue Jan 05 2010 Paul Wouters <paul@xelerance.com> - 1.4.1-1
- Updated to 1.4.1
- Changed %%define to %%global

* Thu Oct 08 2009 Paul Wouters <paul@xelerance.com> - 1.3.4-2
- Bump version

* Thu Oct 08 2009 Paul Wouters <paul@xelerance.com> - 1.3.4-1
- Upgraded to 1.3.4. Security fix with validating NSEC3 records

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 1.3.3-2
- rebuilt with new openssl

* Mon Aug 17 2009 Paul Wouters <paul@xelerance.com> - 1.3.3-1
- Updated to 1.3.3

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sat Jun 20 2009 Paul Wouters <paul@xelerance.com> - 1.3.0-2
- Added missing glob patch to cvs
- Place python macros within the %%with_python check

* Sat Jun 20 2009 Paul Wouters <paul@xelerance.com> - 1.3.0-1
- Updated to 1.3.0
- Added unbound-python sub package. disabled for now
- Patch from svn to fix DLV lookups
- Patches from svn to detect wrong truncated response from BIND 9.6.1 with
  minimal-responses)
- Added Default-Start and Default-Stop to unbound.init
- Re-enabled --enable-sha2
- Re-enabled glob.patch

* Wed May 20 2009 Paul Wouters <paul@xelerance.com> - 1.2.1-7
- unbound-iterator.patch was not commited

* Wed May 20 2009 Paul Wouters <paul@xelerance.com> - 1.2.1-6
- Fix for https://bugzilla.redhat.com/show_bug.cgi?id=499793

* Tue Mar 17 2009 Paul Wouters <paul@xelerance.com> - 1.2.1-5
- Use --nocheck to avoid giving an error on missing unbound-remote certs/keys

* Tue Mar 10 2009 Adam Tkac <atkac redhat com> - 1.2.1-4
- enable DNSSEC only if it is enabled in sysconfig/dnssec

* Mon Mar 09 2009 Adam Tkac <atkac redhat com> - 1.2.1-3
- add DNSSEC support to initscript and enabled it per default
- add requires dnssec-conf

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Feb 10 2009 Paul Wouters <paul@xelerance.com - 1.2.1-1
- updated to 1.2.1

* Sun Jan 18 2009 Tomas Mraz <tmraz@redhat.com> - 1.2.0-2
- rebuild with new openssl

* Wed Jan 14 2009 Paul Wouters <paul@xelerance.com - 1.2.0-1
- Updated to 1.2.0
- Added dependancy on minimum SSL for CVE-2008-5077
- Added dependancy on bc for unbound-munin
- Added minimum requirement of libevent 1.4.5. Crashes with older versions
  (note: libevent is stale in EL-4 and not in EL-5, needs fixing there)
- Removed dependancy on selinux-policy (will get used when available)
- Enable options as per draft-wijngaards-dnsext-resolver-side-mitigation-00.txt
- Enable unwanted-reply-threshold to mitigate against a Kaminsky attack
- Enable val-clean-additional to drop addition unsigned data from signed
  response.
- Removed patches (got merged into upstream)

* Mon Jan  5 2009 Paul Wouters <paul@xelerance.com> - 1.1.1-7
- Modified scandir patch to silently fail when wildcard matches nothing
- Patch to allow unbound-checkconf to find empty wildcard matches

* Mon Jan  5 2009 Paul Wouters <paul@xelerance.com> - 1.1.1-6
- Added scandir patch for trusted-keys-file: option, which
  is used to load multiple dnssec keys in bind file format

* Mon Dec  8 2008 Paul Wouters <paul@xelerance.com> - 1.1.1-4
- Added Requires: for selinux-policy >= 3.5.13-33 for proper SElinux rules.

* Mon Dec  1 2008 Paul Wouters <paul@xelerance.com> - 1.1.1-3
- We did not own the /etc/unbound directory (#474020)
- Fixed cvs anomalies

* Fri Nov 28 2008 Adam Tkac <atkac redhat com> - 1.1.1-2
- removed all obsolete chroot related stuff
- label control certs after generation correctly

* Thu Nov 20 2008 Paul Wouters <paul@xelerance.com> - 1.1.1-1
- Updated to unbound 1.1.1 which fixes a crasher and
  addresses nlnetlabs bug #219

* Wed Nov 19 2008 Paul Wouters <paul@xelerance.com> - 1.1.0-3
- Remove the chroot, obsoleted by SElinux
- Add additional munin plugin links supported by unbound plugin
- Move configuration directory from /var/lib/unbound to /etc/unbound
- Modified unbound.init and unbound.conf to account for chroot changes
- Updated unbound.conf with new available options
- Enabled dns-0x20 protection per default

* Wed Nov 19 2008 Adam Tkac <atkac redhat com> - 1.1.0-2
- unbound-1.1.0-log_open.patch
  - make sure log is opened before chroot call
  - tracked as http://www.nlnetlabs.nl/bugs/show_bug.cgi?id=219
- removed /dev/log and /var/run/unbound and /etc/resolv.conf from
  chroot, not needed
- don't mount files in chroot, it causes problems during updates
- fixed typo in default config file

* Fri Nov 14 2008 Paul Wouters <paul@xelerance.com> - 1.1.0-1
- Updated to version 1.1.0
- Updated unbound.conf's statistics options and remote-control
  to work properly for munin
- Added unbound-munin package
- Generate unbound remote-control  key/certs on first startup
- Required ldns is now 1.4.0

* Wed Oct 22 2008 Paul Wouters <paul@xelerance.com> - 1.0.2-5
- Only call ldconfig in -libs package
- Move configure into build section
- devel subpackage should only depend on libs subpackage

* Tue Oct 21 2008 Paul Wouters <paul@xelerance.com> - 1.0.2-4
- Fix CFLAGS getting lost in build
- Don't enable interface-automatic:yes because that
  causes unbound to listen on 0.0.0.0 instead of 127.0.0.1

* Sun Oct 19 2008 Paul Wouters <paul@xelerance.com> - 1.0.2-3
- Split off unbound-libs, make build verbose 

* Thu Oct  9 2008 Paul Wouters <paul@xelerance.com> - 1.0.2-2
- FSB compliance, chroot fixes, initscript fixes

* Thu Sep 11 2008 Paul Wouters <paul@xelerance.com> - 1.0.2-1
- Upgraded to 1.0.2

* Wed Jul 16 2008 Paul Wouters <paul@xelerance.com> - 1.0.1-1
- upgraded to new release

* Wed May 21 2008 Paul Wouters <paul@xelerance.com> - 1.0.0-2
- Build against ldns-1.3.0

* Wed May 21 2008 Paul Wouters <paul@xelerance.com> - 1.0.0-1
- Split of -devel package, fixed dependancies, make rpmlint happy

* Thu Apr 25 2008 Wouter Wijngaards <wouter@nlnetlabs.nl> - 0.12
- Using parts from ports collection entry by Jaap Akkerhuis.
- Using Fedoraproject wiki guidelines.

* Wed Apr 23 2008 Wouter Wijngaards <wouter@nlnetlabs.nl> - 0.11
- Initial version.
