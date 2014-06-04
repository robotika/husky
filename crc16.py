################################################################################
# Checksum
## @defgroup crc CRC Generation
#  @ingroup doc
#  
#  A 16-bit CRC using one of the CCITT polynomials is used to confirm message 
#  integrity.                                                               \n\n
#
#  <i>Polynomial:</i> x16+x12+x5+1 (0x1021)                                   \n
#
#  <i>Initial value:</i> 0xFFFF                                               \n
#
#  <i>Check constant:</i> 0x1D0F                                            \n\n
#
#  The calculated CRC of the string '123456789' should be 0x29B1              \n
#
#  To confirm CRC implementation, the following process can be used:
#  -# Calculate the CRC of any message
#  -# XOR it with 0xFFFF (bitwise inversion)
#  -# Append it to the original message
#  -# Perform the CRC calculation on the extended message
#  -# Confirm that the new CRC is equal to the check constant (0x1D0F)
#
#  \b Sample \b C \b Code \b for \b table-driven \b CRC \b computation:     \n\n
#  @code
#  /*
#   * crc.h
#   */
#
#  #ifndef __CRC16_H
#  #define __CRC16_H
#
#  /***----------Table-driven crc function----------***/
#  /* Inputs: -size of the character array,           */ 
#  /*              the CRC of which is being computed */
#  /*         - the initial value of the register to  */
#  /*              be used in the calculation         */
#  /*         - a pointer to the first element of     */
#  /*              said character array               */
#  /* Outputs: the crc as an unsigned short int       */
#  unsigned short int crc16(int size, int init_val, char *data);
#
#  #endif
#
#  /*
#   * crc.c
#   */
#
#  #include "crc.h"
#
#  //CRC lookup table for polynomial 0x1021
#  const unsigned short int table[256] =
#  {0, 4129, 8258, 12387, 16516, 20645, 24774, 28903, 33032, 37161, 41290, 
#  45419, 49548, 53677, 57806, 61935, 4657, 528, 12915, 8786, 21173, 
#  17044, 29431, 25302, 37689, 33560, 45947, 41818, 54205, 50076, 62463, 
#  58334, 9314, 13379, 1056, 5121, 25830, 29895, 17572, 21637, 42346, 
#  46411, 34088, 38153, 58862, 62927, 50604, 54669, 13907, 9842, 5649, 
#  1584, 30423, 26358, 22165, 18100, 46939, 42874, 38681, 34616, 63455, 
#  59390, 55197, 51132, 18628, 22757, 26758, 30887, 2112, 6241, 10242, 
#  14371, 51660, 55789, 59790, 63919, 35144, 39273, 43274, 47403, 23285, 
#  19156, 31415, 27286, 6769, 2640, 14899, 10770, 56317, 52188, 64447, 
#  60318, 39801, 35672, 47931, 43802, 27814, 31879, 19684, 23749, 11298, 
#  15363, 3168, 7233, 60846, 64911, 52716, 56781, 44330, 48395, 36200, 
#  40265, 32407, 28342, 24277, 20212, 15891, 11826, 7761, 3696, 65439, 
#  61374, 57309, 53244, 48923, 44858, 40793, 36728, 37256, 33193, 45514, 
#  41451, 53516, 49453, 61774, 57711, 4224, 161, 12482, 8419, 20484, 
#  16421, 28742, 24679, 33721, 37784, 41979, 46042, 49981, 54044, 58239, 
#  62302, 689, 4752, 8947, 13010, 16949, 21012, 25207, 29270, 46570, 
#  42443, 38312, 34185, 62830, 58703, 54572, 50445, 13538, 9411, 5280, 
#  1153, 29798, 25671, 21540, 17413, 42971, 47098, 34713, 38840, 59231, 
#  63358, 50973, 55100, 9939, 14066, 1681, 5808, 26199, 30326, 17941, 
#  22068, 55628, 51565, 63758, 59695, 39368, 35305, 47498, 43435, 22596, 
#  18533, 30726, 26663, 6336, 2273, 14466, 10403, 52093, 56156, 60223, 
#  64286, 35833, 39896, 43963, 48026, 19061, 23124, 27191, 31254, 2801, 
#  6864, 10931, 14994, 64814, 60687, 56684, 52557, 48554, 44427, 40424, 
#  36297, 31782, 27655, 23652, 19525, 15522, 11395, 7392, 3265, 61215, 
#  65342, 53085, 57212, 44955, 49082, 36825, 40952, 28183, 32310, 20053, 
#  24180, 11923, 16050, 3793, 7920};
#
#  /***----------Table-driven crc function----------***/
#  /* Inputs: - size of the character array, the CRC  */
#  /*               of which is being computed        */
#  /*         - the initial value of the register to  */
#  /*               be used in the calculation        */
#  /*         - a pointer to the first element of     */
#  /*               said character array              */
#  /* Outputs: the crc as an unsigned short int       */
#  unsigned short int crc16(int size, int init_val, char *data)
#  {
#        unsigned short int crc = (unsigned short int) init_val;
#        while(size--) {
#              crc = (crc << 8) ^ table[((crc >> 8) ^ *data++) & 0xFFFF];
#        }
#        return crc;
#  }
#  @endcode

  
## Precomputed checksum table. Polynomial 0x1021. 
#
#  Used for performing a 16-bit CRC with polynomial 0x1021
CCIT_CRC_TABLE = (
    0x0, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7, 
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6, 
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485, 
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x840, 0x1861, 0x2802, 0x3823, 
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b, 
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0xa50, 0x3a33, 0x2a12, 
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0xc60, 0x1c41, 
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49, 
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0xe70, 
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0xa1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067, 
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e, 
    0x2b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256, 
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d, 
    0x34e2, 0x24c3, 0x14a0, 0x481, 0x7466, 0x6447, 0x5424, 0x4405, 
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c, 
    0x26d3, 0x36f2, 0x691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634, 
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab, 
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x8e1, 0x3882, 0x28a3, 
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a, 
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0xaf1, 0x1ad0, 0x2ab3, 0x3a92, 
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9, 
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0xcc1, 
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8, 
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0xed1, 0x1ef0
    )



## Perform a 16-bit CRC with CCITT Polynomial 0x1021
#
#  @param  data     A Byte List to checksum
#  @param  init_val The initial value to calculate the checksum with. 
#                   The default value of 0xffff performs a proper checksum.
#  @return          Resultant Checksum (16-bits)
#
#  @pydoc
def ccitt_checksum(data, init_val=0xFFFF):
    """Perform a 16-bit CRC with CCITT Polynomial 0x1021"""
    
    crc = init_val
    for byte in data:
        crc = ((crc << 8) & 0xff00) ^ CCIT_CRC_TABLE[((crc >> 8) ^ byte) & 0xFF]
    return crc

