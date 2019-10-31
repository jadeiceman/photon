Summary:	XML-Parser perl module
Name:		XML-Parser
Version:	2.44
Release:	5%{?dist}
License:	GPL+
URL:		http://search.cpan.org/~toddr/%{name}-%{version}/
Source0:		http://search.cpan.org/CPAN/authors/id/T/TO/TODDR/%{name}-%{version}.tar.gz
%define sha1 XML-Parser=0ab6b932713ec1f9927a1b1c619b6889a5c12849
%if "%{?cross_compile}" != ""
Source1:        http://www.cpan.org/src/5.0/perl-%{perl_version}.tar.gz
Source2:        https://github.com/arsv/perl-cross/releases/download/%{perl_cross_version}/perl-cross-%{perl_cross_version}.tar.gz
%endif
Group:		Development/Tools
Vendor:		VMware, Inc.
Distribution:	Photon
BuildRequires:	expat-devel
BuildRequires:	perl >= 5.28.0
Requires:	expat
Requires:	perl >= 5.28.0
%description
The XML::Parser module is a Perl extension interface to James Clark's XML parser, expat

%global module_name XML-Parser-2.44
%global perl_version 5.28.0
%global perl_cross_version 1.3

%prep
%setup -q

%if "%{?cross_compile}" != ""
export CC="%{_host}-gcc"
export CXX="%{_host}-g++"
export AR="%{_host}-ar"
export AS="%{_host}-as"
export RANLIB="%{_host}-ranlib"
export LD="%{_host}-ld"
export STRIP="%{_host}-strip"

echo "Setting up perl cross-compile..."
%setup -q -b 2 -n perl-cross-%{perl_cross_version}
%setup -q -b 1 -n perl-%{perl_version}
cp -r %{_builddir}/perl-cross-%{perl_cross_version}/* . -v
cp -r %{_builddir}/%{module_name} cpan/ -v

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

make %{?_smp_mflags}

sed -i 's:exec $top/miniperl:exec perl:g' miniperl_top

%ifarch arm %{arm}
%global perl_vendorarch %(%{_builddir}/perl-%{perl_version}/miniperl_top -V:vendorarch | cut -d "'" -f 2)
%endif

cd cpan/%{module_name}

../../miniperl_top Makefile.PL --prefix=%{_prefix} PERL_CORE=1 PERL=../../miniperl_top INSTALLDIRS=vendor

%else
CFLAGS="%{optflags}" perl Makefile.PL INSTALLDIRS=vendor
%endif

make %{?_smp_mflags} OPTIMIZE="%{optflags}"


#perl Makefile.PL --prefix=%{_prefix}
#make %{?_smp_mflags}

%install
cd cpan/%{module_name}
make DESTDIR=%{buildroot} install

%define __perl_version 5.28.0
rm %{buildroot}/%{_libdir}/perl5/%{__perl_version}/*/perllocal.pod

%check
make %{?_smp_mflags} test

%files
%defattr(-,root,root)
%{_libdir}/perl5/*
%{_mandir}/man3/*
%changelog
*   Fri Sep 21 2018 Dweep Advani <dadvani@vmware.com> 2.44-5
-   Consuming perl version upgrade of 5.28.0
*   Tue Nov 14 2017 Alexey Makhalov <amakhalov@vmware.com> 2.44-4
-   Aarch64 support
*   Tue Apr 4 2017 Robert Qi <qij@vmware.com> 2.44-3
-   Update to version 2.44-3 since perl version updated.
*   Tue May 24 2016 Priyesh Padmavilasom <ppadmavilasom@vmware.com> 2.44-2
-   GA - Bump release of all rpms
*   Tue Feb 23 2016 Harish Udaiya Kumar <hudaiyakumar@vmware.com> 2.44-1
-   Upgraded to version 2.44
*   Mon Feb 01 2016 Anish Swaminathan <anishs@vmware.com> 2.41-3
-   Fix for multithreaded perl
*   Wed Jan 13 2016 Anish Swaminathan <anishs@vmware.com> 2.41-2
-   Fix for new perl
*   Thu Oct 23 2014 Divya Thaluru <dthaluru@vmware.com> 2.41-1
-   Initial build. First version
