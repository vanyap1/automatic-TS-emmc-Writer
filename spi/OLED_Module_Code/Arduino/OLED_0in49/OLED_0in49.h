/*****************************************************************************
* | File        :   OLED_0in49.h
* | Author      :   Waveshare team
* | Function    :   0.49inch OLED Module Drive function
* | Info        :
*----------------
* | This version:   V1.0
* | Date        :   2023-05-31
* | Info        :
* -----------------------------------------------------------------------------
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
******************************************************************************/
#ifndef __OLED_0in49_H
#define __OLED_0in49_H

#include "DEV_Config.h"

/********************************************************************************
function:
        Define the full screen height length of the display
********************************************************************************/

#define OLED_0in49_WIDTH  64  // OLED width
#define OLED_0in49_HEIGHT 32// OLED height

void OLED_0in49_Init(void);
void OLED_0in49_Clear(void);
void OLED_0in49_Display(const UBYTE *Image);
void OLED_0in49_Display_RAM(const UBYTE *Image);
#endif
