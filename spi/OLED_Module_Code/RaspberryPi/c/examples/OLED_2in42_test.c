/*****************************************************************************
* | File      	:   OLED_2in42_test.c
* | Author      :   Waveshare team
* | Function    :   1.54inch OLED Module test demo
* | Info        :
*----------------
* |	This version:   V1.0
* | Date        :   2022-07-14
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
#include "test.h"
#include "OLED_2in42.h"

int OLED_2in42_test(void)
{
	printf("2.42inch OLED test demo\n");
	if(DEV_ModuleInit() != 0) {
		return -1;
	}
	  
	printf("OLED Init...\r\n");
	OLED_2in42_Init();
	DEV_Delay_ms(500);
    OLED_2in42_Clear();	
	// 0.Create a new image cache
	UBYTE *BlackImage;
	UWORD Imagesize = ((OLED_2IN42_WIDTH%8==0)? (OLED_2IN42_WIDTH/8): (OLED_2IN42_WIDTH/8+1)) * OLED_2IN42_HEIGHT;
	if((BlackImage = (UBYTE *)malloc(Imagesize)) == NULL) {
			printf("Failed to apply for black memory...\r\n");
			return -1;
	}
	printf("Paint_NewImage\r\n");
	Paint_NewImage(BlackImage, OLED_2IN42_WIDTH, OLED_2IN42_HEIGHT, 270, BLACK);	
	// Paint_SetScale(16);
	printf("Drawing\r\n");
	//1.Select Image
	Paint_SelectImage(BlackImage);
	DEV_Delay_ms(500);
	Paint_Clear(BLACK);

    // 2.Drawing on the image   
    printf("Drawing:page 1\r\n");
    Paint_DrawPoint(20, 10, WHITE, DOT_PIXEL_1X1, DOT_STYLE_DFT);
    Paint_DrawPoint(30, 10, WHITE, DOT_PIXEL_2X2, DOT_STYLE_DFT);
    Paint_DrawPoint(40, 10, WHITE, DOT_PIXEL_3X3, DOT_STYLE_DFT);
    Paint_DrawLine(10, 10, 10, 20, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawLine(20, 20, 20, 30, WHITE, DOT_PIXEL_1X1, LINE_STYLE_SOLID);
    Paint_DrawLine(30, 30, 30, 40, WHITE, DOT_PIXEL_1X1, LINE_STYLE_DOTTED);
    Paint_DrawLine(40, 40, 40, 50, WHITE, DOT_PIXEL_1X1, LINE_STYLE_DOTTED);
    Paint_DrawCircle(60, 30, 15, WHITE, DOT_PIXEL_1X1, DRAW_FILL_EMPTY);
    Paint_DrawCircle(100, 40, 20, WHITE, DOT_PIXEL_1X1, DRAW_FILL_FULL);      
    Paint_DrawRectangle(50, 30, 60, 40, WHITE, DOT_PIXEL_1X1, DRAW_FILL_EMPTY);
    Paint_DrawRectangle(90, 30, 110, 50, BLACK, DOT_PIXEL_1X1, DRAW_FILL_FULL);   
    // 3.Show image on page1
    OLED_2in42_Display(BlackImage);
    DEV_Delay_ms(2000);      
    Paint_Clear(BLACK);
    
    // Drawing on the image
    printf("Drawing:page 2\r\n");     
    Paint_DrawString_EN(10, 0, "waveshare", &Font16, WHITE, WHITE);
    Paint_DrawString_EN(10, 17, "hello world", &Font8, WHITE, WHITE);
    Paint_DrawNum(10, 30, 123.456789, &Font8, 4, WHITE, WHITE);
    Paint_DrawNum(10, 43, 987654, &Font12, 5, WHITE, WHITE);
    // Show image on page2
    OLED_2in42_Display(BlackImage);
    DEV_Delay_ms(2000);  
    Paint_Clear(BLACK);   
    
    // Drawing on the image
    printf("Drawing:page 3\r\n");
    Paint_DrawString_CN(10, 0,"���Abc", &Font12CN, WHITE, WHITE);
    Paint_DrawString_CN(0, 20, "΢ѩ����", &Font24CN, WHITE, WHITE);
    // Show image on page3
    OLED_2in42_Display(BlackImage);
    DEV_Delay_ms(2000);    
    Paint_Clear(BLACK); 

    // Drawing on the image
    printf("Drawing:page 4\r\n");
    GUI_ReadBmp("./pic/waveshare.bmp", 0, 0);
	OLED_2in42_Display(BlackImage);
    DEV_Delay_ms(2000);
    Paint_Clear(BLACK); 

    OLED_2in42_Clear();

    return 0;
}

