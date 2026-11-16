PRODUCT_SOONG_NAMESPACES += vendor/honor/ldy_an00

# Recovery-only OEM boot control; normal-boot provider remains in retained vendor.
PRODUCT_PACKAGES += \
    honor_boot_control_recovery \
    honor_libmtk_bsg_recovery
