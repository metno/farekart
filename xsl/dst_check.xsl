<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" encoding="UTF-8"/>

<!-- DST related templates -->
  <xsl:template name="date-to-absolute-day">
   <xsl:param name="year"/>
   <xsl:param name="month"/>
   <xsl:param name="day"/>

   <xsl:call-template name="julian-day-to-absolute-day">
    <xsl:with-param name="j-day">
     <xsl:call-template name="julian-date-to-julian-day">
      <xsl:with-param name="year" select="$year"/>
      <xsl:with-param name="month" select="$month"/>
      <xsl:with-param name="day" select="$day"/>
     </xsl:call-template>
    </xsl:with-param>
   </xsl:call-template>
  </xsl:template> 

  <xsl:template name="absolute-day-to-date">
   <xsl:param name="abs-day"/>
 
   <xsl:call-template name="absolute-day-to-date">
    <xsl:with-param name="j-day">
     <xsl:call-template name="absolute-day-to-julian-day">
      <xsl:with-param name="abs-day" select="$abs-day"/>
     </xsl:call-template>
    </xsl:with-param>
   </xsl:call-template>
  </xsl:template> 

  <xsl:template name="julian-day-to-absolute-day">
   <xsl:param name="j-day"/>
   <xsl:value-of select="$j-day - 1721425"/>
  </xsl:template>
  
  <xsl:template name="absolute-day-to-julian-day">
   <xsl:param name="abs-day"/>
   <xsl:value-of select="$abs-day + 1721425"/>
  </xsl:template> 

  <xsl:template name="julian-date-to-julian-day">
   <xsl:param name="year"/>
   <xsl:param name="month"/>
   <xsl:param name="day"/>

   <xsl:value-of select="(1461 * ($year + 4800 + ($month - 14) div 12)) div 4 + (367 * ($month - 2 - 12 * (($month - 14) div 12))) div 12 - (3 * (($year + 4900 + ($month - 14) div 12) div 100)) div 4 + $day - 32075"/> 

  </xsl:template>

  <xsl:template name="last-day-of-month">
   <xsl:param name="year"/>
   <xsl:param name="month"/>
   <xsl:choose>
    <xsl:when test="$month = 2 and not($year mod 4) and ($year mod 100 or not($year mod 400))">
     <xsl:value-of select="29"/>
    </xsl:when>
    <xsl:otherwise>
     <xsl:value-of select="substring('312831303130313130313031', 2 * $month - 1,2)"/>
    </xsl:otherwise>
   </xsl:choose>
  </xsl:template>

  <xsl:template name="k-day-on-or-before-abs-day">
   <xsl:param name="abs-day"/>
   <xsl:param name="k"/>
   <xsl:value-of select="$abs-day - (($abs-day - $k) mod 7)"/>
  </xsl:template>

  <xsl:template name="n-th-k-day">
   <!-- The n'th occurance of k in the given month -->
   <!-- Positive n counts from beginning of month; negative from end. -->
   <xsl:param name="n"/>
   <!-- k = the day of the week (0=Sun) -->
   <xsl:param name="k"/>
   <xsl:param name="month"/>
   <xsl:param name="year"/>

   <xsl:choose>
    <xsl:when test="$n > 0">
     <xsl:variable name="k-day-on-or-before">
      <xsl:variable name="abs-day"> 
       <xsl:call-template name="date-to-absolute-day">
        <xsl:with-param name="year" select="$year"/>
        <xsl:with-param name="month" select="$month"/>
        <xsl:with-param name="day" select="7"/>
       </xsl:call-template>
      </xsl:variable>
      <xsl:call-template name="k-day-on-or-before-abs-day">
       <xsl:with-param name="abs-day" select="$abs-day"/>
       <xsl:with-param name="k" select="$k"/>
      </xsl:call-template>
     </xsl:variable>
     <xsl:value-of select="$k-day-on-or-before + 7 * ($n - 1)"/> 
    </xsl:when>
    <xsl:otherwise>
     <xsl:variable name="k-day-on-or-before">
      <xsl:variable name="abs-day">
       <xsl:call-template name="date-to-absolute-day">
        <xsl:with-param name="month" select="$month"/>
        <xsl:with-param name="day">
         <xsl:call-template name="last-day-of-month">
          <xsl:with-param name="month" select="$month"/>
          <xsl:with-param name="year" select="$year"/>
         </xsl:call-template>
        </xsl:with-param>
        <xsl:with-param name="year" select="$year"/>
       </xsl:call-template>
      </xsl:variable>
      <xsl:call-template name="k-day-on-or-before-abs-day">
       <xsl:with-param name="abs-day" select="$abs-day"/>
       <xsl:with-param name="k" select="$k"/>
      </xsl:call-template>
     </xsl:variable>
     <xsl:value-of select="$k-day-on-or-before + 7 * ($n + 1)"/> 
    </xsl:otherwise>
   </xsl:choose> 
  </xsl:template>

  <xsl:template name="day-light-savings-start">
   <xsl:param name="year"/>
   <xsl:call-template name="n-th-k-day">
    <xsl:with-param name="n" select="2"/>
    <xsl:with-param name="k" select="0"/>
    <xsl:with-param name="month" select="3"/>
    <xsl:with-param name="year" select="$year"/>
   </xsl:call-template>
  </xsl:template>

  <xsl:template name="day-light-savings-end">
   <xsl:param name="year"/>
   <xsl:call-template name="n-th-k-day">
    <xsl:with-param name="n" select="-1"/>
    <xsl:with-param name="k" select="0"/>
    <xsl:with-param name="month" select="10"/>
    <xsl:with-param name="year" select="$year"/>
   </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
