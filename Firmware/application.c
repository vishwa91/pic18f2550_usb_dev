/********************************************************************
 FileName:      main.c
 Dependencies:  See INCLUDES section
 Processor:     PIC18F2550
 Hardware:      This firmware is based on custom USB device based on
				PIC18F2550. The schematics can be found in the 
				hardware folder.
 Complier:      Microchip C18 (for PIC18)
 Company:       Microchip Technology, Inc.

 Software License Agreement:
 TODO: Yet to insert a license agreement.
********************************************************************/

/**************************COMMAND RULES****************************
The device will function by receiving commands from a host computer.
The rules are as follows:
1. Every command is 5 characters wide
2. The first field is the identifier for the type of the command.
3. The second field will tell whether it is a read or a write 
   operation. This may be redundant in some cases.

The following commands are supported as of now:
1. DWA0I: This means, it is a direction set operation, a write 
		  operation, the pin RA0 must be modified and set as input.
		  For setting as output, DWA0O
2. PWA0H: A port modify operation. Set RA0 high. For setting as
		  low, PWA0L
3. PRA0X: Read RA0 output bit status.
4. AW00E: Enable AN0. To disable, AW00D
5. ARC01: Read a value from AN1
6. MWS0X: Setup PWM for CCP0
7. MW050: Set PWM duty cycle as 50%. Maximum is 99.
8. UWTXE: Enable UART Transmission. To disable, UWTXD
9. UWRXE: Enable UART Reception. To disable, UWRXD
10.UWTtX: Write the character 't' to the UART port
11.URRXX: Read a character from UART port.

Notes:
1. The following pins are availabe for digital i/0:
   RA0-RA5, RC0-RC2, RC6-RC7, RB2-RB7.
2. The following channels are available for analog operations:
   AN0-AN4, AN8-AN11.
3. PWM period is set at 50 Hz to help servo motors.
4. UART transmission rate is set at 9600bps.
4. The user is responsible for giving the commands in right order.
   Any errors will not be identified by the microcontroller.
*******************************************************************/

// Set the direction of the port as per the command
void dir_cmd( unsigned char port, int pbit, unsigned char dir)
{
	switch(port){
		case 'A':
			if(dir == 'O')
				TRISA &= ~(1 << pbit);
			else if(dir == 'I')
				TRISA |= (1 << pbit);
			break;
		case 'B':
			if(dir == 'O')
				TRISB &= ~(1 << pbit);
			else if(dir == 'I')
				TRISB |= (1 << pbit);
			break;
		case 'C':
			if(dir == 'O')
				TRISC &= ~(1 << pbit);
			else if(dir == 'I')
				TRISC |= (1 << pbit);
			break;		
	}
}

int port_cmd( unsigned char port, int pbit, unsigned char pval)
{
	int ret_val = -1;
	switch(port){
		case 'A':
			if(pval == 'H')
				LATA |= (1 << pbit);
			else if(pval == 'L')
				LATA &= ~(1 << pbit);
			else if(pval == 'X')
				ret_val =  LATA & (1 << pbit);
			break;
		case 'B':
			if(pval == 'H')
				LATB |= (1 << pbit);
			else if(pval == 'L')
				LATB &= ~(1 << pbit);
			else if(pval == 'X')
				ret_val =  LATB & (1 << pbit);
			break;
		case 'C':
			if(pval == 'H')
				LATC |= (1 << pbit);
			else if(pval == 'L')
				LATC &= ~(1 << pbit);
			else if(pval == 'X')
				ret_val = LATC & (1 << pbit);
			break;
	}	
	return ret_val;
}