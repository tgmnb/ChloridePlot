!===============================================================================
! Seasalt for Modal Aerosol Model
!===============================================================================
module seapalt_model
  use shr_kind_mod,   only: r8 => shr_kind_r8, cl => shr_kind_cl
  use ppgrid,         only: pcols, pver
  use modal_aero_data,only: ntot_amode, pnslt=>nSeaPalt

  implicit none
  private

  public :: seapalt_nbin
  public :: seapalt_nnum
  public :: seapalt_names
  public :: seapalt_indices
  public :: seapalt_init
  public :: seapalt_emis
  public :: seapalt_active

  integer, protected :: seapalt_nbin ! = pnslt
  integer, protected :: seapalt_nnum ! = nnum

  character(len=6), protected, allocatable :: seapalt_names(:)
  integer, protected, allocatable :: seapalt_indices(:)

  logical :: seapalt_active = .false.

  real(r8):: emis_scale

contains
  
  !=============================================================================
  !=============================================================================
  subroutine seapalt_init(seapalt_emis_scale)
    use sslt_sections, only: sslt_sections_init
    use constituents,  only: cnst_get_ind
    use rad_constituents, only: rad_cnst_get_info

    real(r8), intent(in) :: seapalt_emis_scale
    integer :: m, l, nspec, ndx
    character(len=32) :: spec_name
    
    seapalt_nbin = pnslt
    seapalt_nnum = pnslt
    allocate(seapalt_names(2*pnslt))
    allocate(seapalt_indices(2*pnslt))

    ndx=0
    do m = 1, ntot_amode
       call rad_cnst_get_info(0, m, nspec=nspec)
       do l = 1, nspec
          call rad_cnst_get_info(0, m, l, spec_name=spec_name )
          if (spec_name(:3) == 'pcl') then
             ndx=ndx+1
             seapalt_names(ndx) = spec_name
             seapalt_names(pnslt+ndx) = 'num_'//spec_name(5:)
             call cnst_get_ind(seapalt_names(     ndx), seapalt_indices(     ndx))
             call cnst_get_ind(seapalt_names(pnslt+ndx), seapalt_indices(pnslt+ndx))
          endif
       enddo
    enddo

    seapalt_active = any(seapalt_indices(:) > 0)
    if (.not.seapalt_active) return

    call sslt_sections_init()

    emis_scale = seapalt_emis_scale

  end subroutine seapalt_init

  !=============================================================================
  !=============================================================================
  subroutine seapalt_emis( u10cubed,  srf_temp, ocnfrc, ncol, cflx )

    use sslt_sections, only: nsections, fluxes, Dg, rdry
    use mo_constants,  only: dns_aer_sst=>seasalt_density, pi

    ! dummy arguments
    real(r8), intent(in) :: u10cubed(:)
    real(r8), intent(in) :: srf_temp(:)
    real(r8), intent(in) :: ocnfrc(:)
    integer,  intent(in) :: ncol
    real(r8), intent(inout) :: cflx(:,:)

    ! local vars
    integer  :: mn, mm, ibin, isec, i
    real(r8) :: fi(ncol,nsections)

    real(r8) :: sst_sz_range_lo (pnslt)
    real(r8) :: sst_sz_range_hi (pnslt)

    if (pnslt==4) then
       sst_sz_range_lo (:) = (/ 0.08e-6_r8, 0.02e-6_r8, 0.3e-6_r8,  1.0e-6_r8 /) ! accu, aitken, fine, coarse
       sst_sz_range_hi (:) = (/ 0.3e-6_r8,  0.08e-6_r8, 1.0e-6_r8, 10.0e-6_r8 /)
    else if (pnslt==3) then
       sst_sz_range_lo (:) =  (/ 0.08e-6_r8,  0.02e-6_r8,  1.0e-6_r8 /)  ! accu, aitken, coarse
       sst_sz_range_hi (:) =  (/ 1.0e-6_r8,   0.08e-6_r8, 10.0e-6_r8 /)
    endif

    fi(:ncol,:nsections) = fluxes( srf_temp, u10cubed, ncol )

    do ibin = 1,pnslt
       mm = seapalt_indices(ibin)
       mn = seapalt_indices(pnslt+ibin)
       
       if (mn>0) then
          do i=1, nsections
             if (Dg(i).ge.sst_sz_range_lo(ibin) .and. Dg(i).lt.sst_sz_range_hi(ibin)) then
                cflx(:ncol,mn)=cflx(:ncol,mn)+fi(:ncol,i)*ocnfrc(:ncol)*emis_scale  !++ ag: scale sea-salt
             endif
          enddo
       endif

       cflx(:ncol,mm)=0.0_r8
       do i=1, nsections
          if (Dg(i).ge.sst_sz_range_lo(ibin) .and. Dg(i).lt.sst_sz_range_hi(ibin)) then
             cflx(:ncol,mm)=cflx(:ncol,mm)+fi(:ncol,i)*ocnfrc(:ncol)*emis_scale  &   !++ ag: scale sea-salt
                  *4._r8/3._r8*pi*rdry(i)**3*dns_aer_sst  ! should use dry size, convert from number to mass flux (kg/m2/s)
          endif
       enddo

    enddo

  end subroutine seapalt_emis

end module seapalt_model
