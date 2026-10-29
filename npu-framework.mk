PRODUCT_SOONG_NAMESPACES += vendor/honor/ldy_an00
PRODUCT_PACKAGES += \
    honor_npu_libneuronusdk_adapter_mtk \
    honor_npu_libapuwareapusys_v2_mtk \
    honor_npu_libapuwarehmp_mtk \
    honor_npu_libapuwareutils_mtk \
    honor_npu_libapuwareutils_v2_mtk \
    honor_npu_libmvpu_engine_pub_mtk \
    honor_npu_libmvpu_pattern_pub_mtk \
    honor_npu_vendor_mediatek_hardware_apuware_apusys_2_0 \
    honor_npu_vendor_mediatek_hardware_apuware_apusys_2_1 \
    honor_npu_vendor_mediatek_hardware_apuware_apusys_V5_ndk \
    honor_npu_vendor_mediatek_hardware_apuware_hmp_1_0 \
    honor_npu_vendor_mediatek_hardware_apuware_utils_1_0 \
    honor_npu_vendor_mediatek_hardware_apuware_utils_2_0 \
    honor_npu_vendor_mediatek_hardware_apuware_utils_V1_ndk

PRODUCT_COPY_FILES += \
    vendor/honor/ldy_an00/config/npu/public.libraries-mtk.txt:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/public.libraries-mtk.txt
