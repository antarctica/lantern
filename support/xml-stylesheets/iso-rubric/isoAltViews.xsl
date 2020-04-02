<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl" exclude-result-prefixes="xd" version="2.0">

    <xsl:param name="xpath"/>
    <!--This is the old param used by nmmrview-->
    <xsl:param name="xml"/>
    <!--Docucomp provides all query string params as XSLT params-->
    <xsl:param name="view"/>
    <!--Docucomp provides all query string params as XSLT params-->

    <!-- passed-in global params are optional, and defaulted -->
    <xsl:param name="docucompUrl" select="'https://www.ngdc.noaa.gov/docucomp'"/>
    <xsl:param name="wafBaseUrl" select="'https://www.ngdc.noaa.gov/metadata/published/'"/>

    <!--parse the wafName from the 'xml' param
	 - truncate from '/iso' onward -->
    <xsl:param name="wafName" select="substring-before($xml, '/iso')"/>

    <xsl:template name="isoAltViews">
        <xsl:variable name="xmlPath">
            <xsl:choose>
                <xsl:when test="$xpath"><!-- old nmmrview param -->
                    <xsl:value-of select="$xpath"/>
                </xsl:when>
                <xsl:otherwise><!-- new Docucomp param -->
                    <xsl:value-of select="$xml"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="wafFlavor">
            <xsl:choose>
                <xsl:when test="contains($xmlPath, '/iso/')"><xsl:text>/iso/</xsl:text></xsl:when>
                <xsl:when test="contains($xmlPath, '/iso_u/')"><xsl:text>/iso_u/</xsl:text></xsl:when>
                <!-- no default for now; assumes either /iso/ or /iso_u/ -->
            </xsl:choose>
        </xsl:variable>

        <!--build link back to WAF-->
        <a href="{$wafBaseUrl}{$wafName}{$wafFlavor}" title=""><i>Back to Collection <xsl:value-of select="$wafName"/></i></a>
        <br/>

        <i>View Metadata As: </i>


        <xsl:comment select="concat('xmlPath=',$xmlPath, '...')"/>
        <xsl:choose>
            <!-- These views make sense only for resolved records in the iso/ WAF -->
            <xsl:when test="contains($xmlPath, '/iso/')">
                <xsl:choose>
                    <xsl:when test="$view='getDataView'">
                        <b>Get Data, </b>
                    </xsl:when>
                    <xsl:otherwise>
                        <a title="View links to get the data from this dataset" href="/metaview/page?xml={$xmlPath}&amp;view=getDataView&amp;header=none">Get Data</a>, </xsl:otherwise>
                </xsl:choose>
                <xsl:choose>
                    <xsl:when test="$view='iso2faq/FAQ_ISO'">
                        <b>FAQ, </b>
                    </xsl:when>
                    <xsl:otherwise>
                        <a title="View as FAQ page" href="/metaview/page?xml={$xmlPath}&amp;view=iso2faq/FAQ_ISO">FAQ</a>, </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="$view='xml2text/xml-to-text-ISO'">
                <b>HTML, </b>
            </xsl:when>
            <xsl:otherwise>
                <a title="View as ISO indented text" href="/metaview/page?xml={$xmlPath}&amp;view=xml2text/xml-to-text-ISO">HTML, </a>
            </xsl:otherwise>
        </xsl:choose>
        <a title="View raw XML" href="https://www.ngdc.noaa.gov/metadata/published/{$xmlPath}">19139 XML</a>
        <!--full URL since only prod server has WAFs -->
        <br/>
        <i>Assess Metadata For: </i>
        <xsl:choose>
            <!-- These views make sense only for resolved records in the iso/ WAF -->
            <xsl:when test="contains($xmlPath, '/iso/')">

                <xsl:choose>
                    <xsl:when test="$view='isoRubricHTML'">
                        <b>Completeness, </b>
                    </xsl:when>
                    <xsl:otherwise>
                        <a title="View as ISO Rubric Report" href="/metaview/page?xml={$xmlPath}&amp;view=rubricv2/recordHTML&amp;header=none">Completeness, </a>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:choose>
                    <xsl:when test="$view='doiRubricHTML'">
                        <b>DOI Readiness, </b>
                    </xsl:when>
                    <xsl:otherwise>
                        <a title="View as DOI Rubric Report" href="/metaview/page?xml={$xmlPath}&amp;view=doiRubricHTML">DOI Readiness, </a>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:choose>
                    <xsl:when test="contains($xmlPath, '/iso/')">
                        <xsl:choose>
                            <xsl:when test="$view='CSWRubricHTML'">
                                <b>CSW Readiness, </b>
                            </xsl:when>
                            <xsl:otherwise>
                                <a title="View links to get the data from this dataset" href="/metaview/page?xml={$xmlPath}&amp;view=CSWRubricHTML">CSW Readiness, </a>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="$view='ISO19115Components-HTMLTable'">
                <b>Components</b>
            </xsl:when>
            <xsl:otherwise>
                <a title="View as HTML components table" href="/metaview/page?xml={$xmlPath}&amp;view=ISO19115Components-HTMLTable">Components</a>
            </xsl:otherwise>
        </xsl:choose>

        <!-- These views make sense resolved or unresolved records in the iso/ or iso_u/ WAFs -->

        <!-- These views make sense only for resolved records in the iso/ WAF -->

        <hr/>

    </xsl:template>

</xsl:stylesheet>