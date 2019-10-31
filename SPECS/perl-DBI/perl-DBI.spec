# Got the intial spec from Fedora and modified it
# Filter unwanted dependencies
%global __requires_exclude %{?__requires_exclude|%__requires_exclude|}^perl\\(RPC::\\)

# According to documentation, module using Coro is just:
# A PROOF-OF-CONCEPT IMPLEMENTATION FOR EXPERIMENTATION.
# Omit Coro support on bootsrap bacause perl-DBI is pulled in by core
# perl-CPANPLUS.
%bcond_without coro

%global perl_version 5.28.0
%global perl_cross_version 1.3

Summary:        A database access API for perl
Name:           perl-DBI
Version:        1.641
Release:        1%{?dist}
Group:          Development/Libraries
License:        GPL+ or Artistic
URL:            http://dbi.perl.org/
# The source tarball must be repackaged to remove the DBI/FAQ.pm, since the
# license is not a FSF free license.
Source0:        https://cpan.metacpan.org/authors/id/T/TI/TIMB/DBI-%{version}.tar.gz
#Source0:        DBI-%{version}_repackaged.tar.gz
%if "%{?cross_compile}" != ""
Source1:        http://www.cpan.org/src/5.0/perl-%{perl_version}.tar.gz
Source2:        https://github.com/arsv/perl-cross/releases/download/%{perl_cross_version}/perl-cross-%{perl_cross_version}.tar.gz
%endif
%define sha1 DBI=d14c34fac2dd058905b0b8237a4ca8b86eed6f5d
Vendor:		VMware, Inc.
Distribution:	Photon
BuildRequires:  perl >= %{perl_version}
Requires:	perl >= %{perl_version}

%description
DBI is a database access Application Programming Interface (API) for
the Perl Language. The DBI API Specification defines a set of
functions, variables and conventions that provide a consistent
database interface independent of the actual database being used.

%prep
%setup -q -n DBI-%{version}
for F in lib/DBD/Gofer.pm; do
    iconv -f ISO-8859-1 -t UTF-8 < "$F" > "${F}.utf8"
    touch -r "$F" "${F}.utf8"
    mv "${F}.utf8" "$F"
done
chmod 644 ex/*
chmod 744 dbixs_rev.pl
# Fix shell bangs
for F in dbixs_rev.pl ex/corogofer.pl; do
    perl -MExtUtils::MakeMaker -e "ExtUtils::MM_Unix->fixin(q{$F})"
done

rm lib/DBD/Gofer/Transport/corostream.pm
sed -i -e '/^lib\/DBD\/Gofer\/Transport\/corostream.pm$/d' MANIFEST

# Remove RPC::Pl* reverse dependencies due to security concerns,
# CVE-2013-7284, bug #1051110
for F in lib/Bundle/DBI.pm lib/DBD/Proxy.pm lib/DBI/ProxyServer.pm \
        dbiproxy.PL t/80proxy.t; do
    rm "$F"
    sed -i -e '\|^'"$F"'|d' MANIFEST
done
sed -i -e 's/"dbiproxy$ext_pl",//' Makefile.PL
# Remove Win32 specific files to avoid unwanted dependencies
for F in lib/DBI/W32ODBC.pm lib/Win32/DBIODBC.pm; do
    rm "$F"
    sed -i -e '\|^'"$F"'|d' MANIFEST
done

%if "%{?cross_compile}" != ""
echo "Setting up perl cross-compile..."
%setup -q -b 2 -n perl-cross-%{perl_cross_version}
%setup -q -b 1 -n perl-%{perl_version}
cp -r %{_builddir}/perl-cross-%{perl_cross_version}/* . -v
cp -r %{_builddir}/DBI-%{version} cpan/ -v
%endif

%build
%if "%{?cross_compile}" != ""
CONFIGURE_OPTS="\
    --prefix=%{_prefix} \
    --target=%{_host} \
    -Dvendorprefix=%{_prefix} \
    -Dman1dir=%{_mandir}/man1 \
    -Dman3dir=%{_mandir}/man3 \
    -Duseshrplib \
    -Dusethreads \
    -DPERL_RANDOM_DEVICE=/dev/erandom \
    --only-mod= \
"
./configure $CONFIGURE_OPTS

# Make miniperl
make %{?_smp_mflags}

#sed -i 's:exec $top/miniperl:exec perl:g' miniperl_top
cd cpan/DBI-%{version}
../../miniperl_top Makefile.PL PERL_CORE=1 PERL=../../miniperl_top INSTALLDIRS=vendor

%else
CFLAGS="%{optflags}" perl Makefile.PL INSTALLDIRS=vendor
%endif

make %{?_smp_mflags} OPTIMIZE="%{optflags}"

%install
%if "%{?cross_compile}" != ""
# Install spits out extra files because of the cross compile, so ignore them
%define _unpackaged_files_terminate_build 0
cd cpan/DBI-%{version}
%endif

make pure_install DESTDIR=%{buildroot}
find %{buildroot} -type f -name .packlist -exec rm -f {} ';'
find %{buildroot} -type f -name '*.bs' -empty -exec rm -f {} ';'
%{_fixperms} '%{buildroot}'/*

%ifarch arm %{arm}
%global perl_vendorarch %(%{_builddir}/perl-%{perl_version}/miniperl_top -V:vendorarch | cut -d "'" -f 2)
%endif

%check
make test

%files
%{_bindir}/dbipro*
%{_bindir}/dbilogstrip
%{perl_vendorarch}/dbi*.p*
%{perl_vendorarch}/DBD/
%{perl_vendorarch}/DBI/
%{perl_vendorarch}/auto/DBI/
%{_mandir}/man1/*.1*
%{_mandir}/man3/*.3*

%changelog
*   Fri Sep 21 2018 Dweep Advani <dadvani@vmware.com> 1.641-1
-   Update to version 1.641
*   Mon Apr 3 2017 Robert Qi <qij@vmware.com> 1.636-1
-   Upgraded to 1.636
*   Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 1.634-2
-   GA - Bump release of all rpms
*   Thu Jan 21 2016 Anish Swaminathan <anishs@vmware.com> 1.634-1
-   Upgrade version
*   Fri Apr 3 2015 Divya Thaluru <dthaluru@vmware.com> 1.633-1
-   Initial version.
