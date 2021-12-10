<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.14.0-Pi" minScale="1e+08" maxScale="0" hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal mode="0" enabled="0" fetchMode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Value"/>
  </customproperties>
  <pipe>
    <rasterrenderer nodataColor="" type="paletted" opacity="1" alphaBand="-1" band="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry alpha="255" color="#a4d959" label="Grass" value="1"/>
        <paletteEntry alpha="255" color="#2fa600" label="Broadleaved Trees" value="2"/>
        <paletteEntry alpha="255" color="#507000" label="Coniferous Trees" value="3"/>
        <paletteEntry alpha="255" color="#ae0000" label="Impervious/Artificial" value="4"/>
        <paletteEntry alpha="255" color="#eedb85" label="Bare Soil" value="5"/>
        <paletteEntry alpha="255" color="#4492ce" label="Water" value="6"/>
      </colorPalette>
      <colorramp type="randomcolors" name="[source]"/>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="0"/>
    <huesaturation colorizeOn="0" colorizeRed="255" grayscaleMode="0" colorizeBlue="128" saturation="0" colorizeStrength="100" colorizeGreen="128"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
